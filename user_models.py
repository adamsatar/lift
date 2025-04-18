from sqlalchemy import MetaData
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


user_metadata = MetaData()

class UserBase(SQLModel):
    metadata = user_metadata

class Workout(UserBase, table=True):
    __tablename__ = "workouts"
    uuid: str = Field(primary_key=True)
    date: str

    exercises: List["Exercise"] = Relationship(back_populates="workout")
    sequence: List["WorkoutSequence"] = Relationship(back_populates="workout")

class WorkoutSequence(UserBase, table=True):
    __tablename__ = "workout_sequence"
    workout_uuid: str = Field(foreign_key="workouts.uuid", primary_key=True)
    exercise_id: int = Field(primary_key=True)
    sequence_number: int

    workout: Optional[Workout] = Relationship(back_populates="sequence")

class Exercise(UserBase, table=True):
    __tablename__ = "exercises"
    id: Optional[int] = Field(default=None, primary_key=True)
    workout_uuid: str = Field(foreign_key="workouts.uuid")
    exercise_id: int = Field()
    set_number: int
    weight: Optional[float]
    reps: Optional[int]
    duration: Optional[int]
    rest: Optional[int]
    note: Optional[str]

    workout: Optional[Workout] = Relationship(back_populates="exercises")

def create_all_user_tables(engine):
    user_metadata.create_all(engine)