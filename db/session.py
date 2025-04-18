from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from db.user_models import UserBase,Workout, WorkoutSequence, Exercise
from db.system_models import SystemBase,Equipment,MuscleGroup,ExerciseCatalog,exercise_muscle_map


# ------------------------
# User-log database setup
# ------------------------
USER_DB_URL = "sqlite:///user_log.db"
user_engine = create_engine(USER_DB_URL, echo=False, future=True)
UserSessionLocal = sessionmaker(bind=user_engine, autoflush=False, autocommit=False, future=True)

def init_user_db():
    """
    Create only the user-log tables: workouts and exercises.
    """
    UserBase.metadata.create_all(
        user_engine,
        tables=[
            Workout.__table__,
            WorkoutSequence.__table__,
            Exercise.__table__,

        ]
    )

def get_user_session():
    """Return a new Session for the user-log DB."""
    return UserSessionLocal()

# ------------------------
# System database setup
# ------------------------
SYSTEM_DB_URL = "sqlite:///system.db"
system_engine = create_engine(SYSTEM_DB_URL, echo=False, future=True)
SystemSessionLocal = sessionmaker(bind=system_engine, autoflush=False, autocommit=False, future=True)

def init_system_db():
    """
    Create only the system tables: equipment, muscle_groups,
    exercise_catalog, exercise_muscle_map, workout_sequence.
    """
    SystemBase.metadata.create_all(
        system_engine,
        tables=[
            Equipment.__table__,
            MuscleGroup.__table__,
            ExerciseCatalog.__table__,
            exercise_muscle_map
        ]
    )

def get_system_session():
    """Return a new Session for the system DB."""
    return SystemSessionLocal()

# ------------------------
# Combined initialization
# ------------------------
def init_db():
    """
    Initialize both system and user databases.
    """
    init_system_db()
    init_user_db()