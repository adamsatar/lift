
import yaml
import pandas as pd
import uuid
from sqlmodel import Session, select
from system_models import Equipment, MuscleGroup, ExerciseCatalog, ExerciseMuscleLink
from user_models import Workout, Exercise, WorkoutSequence


def seed_system_db(
    system_engine,

    equipment_yaml="config/equipment.yaml",
    muscle_groups_yaml="config/muscle_groups.yaml",
    catalog_yaml="config/default_catalog.yaml"
):
    with Session(system_engine) as session:
        # Seed Equipment
        if not session.exec(select(Equipment)).first():
            with open(equipment_yaml) as f:
                equipment_items = yaml.safe_load(f)
            equipment_map = {}
            for item in equipment_items:
                eq = Equipment(
                    name=item["name"],
                    default_weight=item.get("default_weight", 0.0),
                    track_weight=item.get("track_weight", True),
                    has_resistance_levels=item.get("has_resistance_levels", False)
                )
                session.add(eq)
                equipment_map[eq.name] = eq
            session.commit()

        # Seed Muscle Groups
        if not session.exec(select(MuscleGroup)).first():
            with open(muscle_groups_yaml) as f:
                muscle_names = yaml.safe_load(f)
            muscle_map = {}
            for name in muscle_names:
                mg = MuscleGroup(name=name)
                session.add(mg)
                muscle_map[mg.name] = mg
            session.commit()

        # Seed Exercise Catalog
        if not session.exec(select(ExerciseCatalog)).first():
            with open(catalog_yaml) as f:
                catalog_entries = yaml.safe_load(f)
            for entry in catalog_entries:
                cat = ExerciseCatalog(
                    name=entry["exercise"],
                    equipment_id=equipment_map[entry["equipment"]].id,
                    weight=entry.get("weight", 0.0),
                    measured_by=entry.get("measured_by", "Reps")
                )
                session.add(cat)
                session.flush()  # Ensure cat.id is populated
                for muscle in entry.get("muscle_groups", []):
                    if muscle in muscle_map:
                        link = ExerciseMuscleLink(
                            exercise_id=cat.id,
                            muscle_group_id=muscle_map[muscle].id
                        )
                        session.add(link)
            session.commit()


def seed_user_db(    user_engine,system_engine,
                     csv_path="exercises_clean.csv"):
    df = pd.read_csv(csv_path)
    grouped_by_date = df.groupby("date")

    # Build catalog name → id map from system DB
    with Session(system_engine) as sys_session:
        catalog_map = { c.name: c.id for c in sys_session.exec(select(ExerciseCatalog)).all() }

    with Session(user_engine) as session:

        for date, group in grouped_by_date:
            workout_uuid = str(uuid.uuid5(uuid.NAMESPACE_DNS, date))
            workout = Workout(uuid=workout_uuid, date=date)
            session.add(workout)
            session.commit()

            for i, (exercise_name, ex_group) in enumerate(group.groupby("exercise"), start=1):
                exercise_id = catalog_map.get(exercise_name)
                ws = WorkoutSequence(
                    workout_uuid=workout_uuid,
                    exercise_id=exercise_id,
                    sequence_number=i
                )
                session.add(ws)

            for _, row in group.iterrows():
                ex = Exercise(
                    workout_uuid=workout_uuid,
                    exercise_id=catalog_map.get(row["exercise"]),
                    set_number=row["set_number"],
                    weight=row.get("weight"),
                    reps=row.get("reps"),
                    duration=row.get("duration"),
                    rest=row.get("rest"),
                    note=row.get("note")
                )
                session.add(ex)

            session.commit()


def seed_all(system_engine,    user_engine):
    seed_system_db(system_engine)
    seed_user_db(user_engine,system_engine)