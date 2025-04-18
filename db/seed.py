import yaml
import pandas as pd
import uuid

from db.user_models import Workout,Exercise,WorkoutSequence
from db.system_models import Equipment,MuscleGroup,ExerciseCatalog
from db.session import get_user_session, get_system_session


def seed_system_db(
    equipment_yaml="config/equipment.yaml",
    muscle_groups_yaml="config/muscle_groups.yaml",
    catalog_yaml="config/default_catalog.yaml"
):
    sess = get_system_session()

    # Seed Equipment
    if sess.query(Equipment).first() is None:
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
            sess.add(eq)
            equipment_map[eq.name] = eq
        sess.commit()

    # Seed Muscle Groups
    if sess.query(MuscleGroup).first() is None:
        with open(muscle_groups_yaml) as f:
            muscle_names = yaml.safe_load(f)
        muscle_map = {}
        for name in muscle_names:
            mg = MuscleGroup(name=name)
            sess.add(mg)
            muscle_map[mg.name] = mg
        sess.commit()

    # Seed Exercise Catalog
    # if sess.query(ExerciseCatalog).first() is None:
    #     # if 'equipment_map' not in locals():
    #     equipment_map = {e.exercise: e for e in sess.query(Equipment).all()}
    #     # if 'muscle_map' not in locals():
    #     muscle_map = {m.exercise: m for m in sess.query(MuscleGroup).all()}

    with open(catalog_yaml) as f:
        catalog_entries = yaml.safe_load(f)
    for entry in catalog_entries:
        cat = ExerciseCatalog(
            name=entry["exercise"],
            equipment_name=entry["equipment"],
            weight=entry['weight'],
            measured_by=entry["measured_by"]
        )
        sess.add(cat)

        for muscle in entry.get("muscle_groups", []):
            if muscle in muscle_map:
                cat.muscles.append(muscle_map[muscle])

        sess.commit()

    # for entry in catalog_entries:
    #     cat = ExerciseCatalog(
    #         name=entry["exercise"],
    #         equipment_name=entry["equipment"],
    #         weight=entry['weight'],
    #         measured_by=entry["measured_by"]
    #     )
    #     sess.add(cat)
    #
    #     for muscle in entry.get("muscle_groups", []):
    #         # if muscle in muscle_map:
    #         cat.muscles.append(muscle)
    #
    #     sess.commit()

    sess.close()

def seed_user_db(csv_path="exercises_clean.csv"):
    """
    Read the CSV and populate the workouts and exercises tables.
    Expects columns: date, exercise, set_number, weight, reps, duration, rest, note.
    """
    sess = get_user_session()
    df = pd.read_csv(csv_path)

    # # group entries by date
    # d = {cat:group for cat,group in df.groupby('date')}
    # for k, v in d.items():
    #     print(k,v)

    # group entries by date
    workouts_by_date = {date: group for date, group in df.groupby('date')}
    sequences = {}

    for date, date_group_df in workouts_by_date.items():


        workout = Workout(uuid=str(uuid.uuid5(uuid.NAMESPACE_DNS, date)),date=date)
        sess.add(workout)

        exercises = list(date_group_df.groupby('exercise'))
        # sequences[date] = [(exercise[0], idx) for idx, exercise in enumerate(exercises, start=1)]

        for idx, exercise in enumerate(exercises, start=1):

            workout_sequence = WorkoutSequence(workout_uuid=workout.uuid,exercise=exercise[0],sequence_number=idx)
            sess.add(workout_sequence)

        for _, row in date_group_df.iterrows():
            ex = Exercise(
                workout_uuid=workout.uuid,
                exercise=row['exercise'],
                set_number=row['set_number'],
                weight=row['weight'],
                reps=row['reps'],
                duration=row['duration'],
                rest=row['rest'],
                note=row['note']
            )
            sess.add(ex)
        sess.commit()

    sess.close()

def seed_all():
    """Run all three in sequence."""
    seed_system_db()
    seed_user_db()