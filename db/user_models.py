from sqlalchemy import Column, String, Integer, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

UserBase = declarative_base()

class Workout(UserBase):
    __tablename__ = "workouts"
    uuid = Column(String, primary_key=True, index=True)
    date = Column(String, nullable=False)

    exercises = relationship("Exercise", back_populates="workout", cascade="all, delete-orphan")
    sequence = relationship("WorkoutSequence", back_populates="workout", cascade="all, delete-orphan")

class WorkoutSequence(UserBase):
    __tablename__ = "workout_sequence"
    workout_uuid = Column(String, ForeignKey("workouts.uuid", ondelete="CASCADE"), primary_key=True)
    exercise = Column(Integer, primary_key=True)
    sequence_number = Column(Integer, nullable=False)

    workout = relationship("Workout", back_populates="sequence")

class Exercise(UserBase):
    __tablename__ = "exercises"
    id = Column(Integer, primary_key=True, autoincrement=True)
    workout_uuid = Column(String, ForeignKey("workouts.uuid", ondelete="CASCADE"))
    exercise = Column(Integer, nullable=False)  # FK to system DB not enforced
    set_number = Column(Integer, nullable=False)
    weight = Column(Float)
    reps = Column(Integer)
    duration = Column(Integer)
    rest = Column(Integer)
    note = Column(String)

    workout = relationship("Workout", back_populates="exercises")