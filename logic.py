from typing import List, Dict
from sqlmodel import Session, select
from user_models import Workout, Exercise
from system_models import ExerciseCatalog
import pandas as pd
from sqlalchemy import create_engine

class SystemService:
    def __init__(self):
        self.engine = create_engine("sqlite:///system.db")

    def __enter__(self):
        self.session = Session(self.engine)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def get_exercise_name_map(self) -> Dict[int, str]:
        return {e.id: e.name for e in self.session.exec(select(ExerciseCatalog)).all()}

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

    def get_workout_uuid_map(self) -> Dict[str, str]:
        return {f"{w.date} ({w.uuid[:8]})": w.uuid for w in self.get_all_workouts()}

    def get_workout_display_strings(self):
        uuid_map = self.get_workout_uuid_map()
        return uuid_map.keys()

    def get_exercises_for_workout(self, workout_uuid: str) -> List[Exercise]:
        return self.session.exec(select(Exercise).where(Exercise.workout_uuid == workout_uuid)).all()

def build_exercise_dataframe(exercises: List[Exercise], name_map: Dict[int, str]) -> pd.DataFrame:
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