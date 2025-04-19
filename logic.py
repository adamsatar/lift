from typing import List, Dict
from sqlmodel import Session, select
from user_models import Workout, Exercise
from system_models import ExerciseCatalog
import pandas as pd
from sqlalchemy import create_engine
import plotly.express as px

class SystemService:
    def __init__(self):
        self.engine = create_engine("sqlite:///system.db")

    def __enter__(self):
        self.session = Session(self.engine)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def get_exercise_catalog(self) -> List[ExerciseCatalog]:
        return self.session.exec(select(ExerciseCatalog)).all()

    def get_exercise_name_map(self) -> Dict[int, str]:
        return {e.id: e.name for e in self.get_exercise_catalog()}

class UserService:
    def __init__(self):
        self.engine = create_engine("sqlite:///user_log.db")

    def __enter__(self):
        self.session = Session(self.engine)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def get_all_workouts(self) -> List[Workout]:
        return self.session.exec(select(Workout)).all()

    def get_workout_uuid_to_date_map(self):
        return {w.uuid: w.date for w in self.get_all_workouts()}

    def get_workout_uuid_map(self) -> Dict[str, str]:
        return {f"{w.date} ({w.uuid[:8]})": w.uuid for w in self.get_all_workouts()}

    def get_workout_display_strings(self):
        uuid_map = self.get_workout_uuid_map()
        return uuid_map.keys()

    def get_exercises_for_workout(self, workout_uuid: str) -> List[Exercise]:
        return self.session.exec(select(Exercise).where(Exercise.workout_uuid == workout_uuid)).all()

    def get_all_exercises(self) -> List[Exercise]:
        return self.session.exec(select(Exercise)).all()

    def get_plotly_volume_chart(self) -> pd.DataFrame:
        workouts = self.get_all_workouts()
        records = []

        for workout in workouts:
            exercises = self.get_exercises_for_workout(workout.uuid)
            volume = sum((e.weight or 0) * (e.reps or 0) for e in exercises)
            records.append({
                "Date": workout.date,
                "Workout": workout.uuid[:8],
                "Volume": volume
            })

        df = pd.DataFrame(records)

        return px.line(df, x="Date", y="Volume", title="Training Volume Over Time", markers=True)



def get_exercise_df(exercises: List[Exercise], name_map: Dict[int, str]) -> pd.DataFrame:
    df = {
        "Exercise": [],
        "Set": [],
        "Weight": [],
        "Reps": [],
        "Duration": [],
        "Rest": [],
        "Note": []
    }
    for e in exercises:
        df["Exercise"].append(name_map.get(e.exercise_id, "Unknown"))
        df["Set"].append(e.set_number)
        df["Weight"].append(e.weight)
        df["Reps"].append(e.reps)
        df["Duration"].append(e.duration)
        df["Rest"].append(e.rest)
        df["Note"].append(e.note)

    return pd.DataFrame(df)

def get_all_exercises_df() -> pd.DataFrame:

    with UserService() as usr_svc, SystemService() as sys_svc:
        exercises = usr_svc.get_all_exercises()
        # Map workout UUID to date
        workout_map = usr_svc.get_workout_uuid_to_date_map()
        name_map = sys_svc.get_exercise_name_map()

    # Build DataFrame
    data = []
    for e in exercises:
        data.append({
            "Date": workout_map[e.workout_uuid],
            "Exercise": name_map[e.exercise_id],
            "Set": e.set_number,
            "Weight": e.weight,
            "Reps": e.reps,
            "Duration": e.duration,
            "Rest": e.rest,
            "Note": e.note,
        })


    return pd.DataFrame(data)

def get_plotly_volume_chart():
    exercises_df = get_all_exercises_df()
    exercises_df["Date"] = pd.to_datetime(exercises_df["Date"], format="%m/%d/%Y")
    exercises_df["Volume"] = exercises_df["Weight"] * exercises_df["Reps"]
    volume_df = exercises_df.groupby(["Date", "Exercise"], as_index=False)["Volume"].sum()

    # Create interactive Plotly chart
    fig = px.line(volume_df, x="Date", y="Volume", color="Exercise",
                  title="Volume Over Time (All Exercises)",
                  markers=True)
    fig.update_layout(legend_title_text="Exercise")

    return fig
