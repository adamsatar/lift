from sqlalchemy import Column, String, Integer, Float, Boolean, Table, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

SystemBase = declarative_base()

exercise_muscle_map = Table(
    "exercise_muscle_map", SystemBase.metadata,
    Column("exercise_id", Integer, ForeignKey("exercise_catalog.id"), primary_key=True),
    Column("muscle_group_id", Integer, ForeignKey("muscle_groups.id"), primary_key=True)
)

class Equipment(SystemBase):
    __tablename__ = "equipment"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    default_weight = Column(Float, default=0)
    track_weight = Column(Boolean, default=True)
    has_resistance_levels = Column(Boolean, default=False)

    catalog_entries = relationship("ExerciseCatalog", back_populates="equipment")

class MuscleGroup(SystemBase):
    __tablename__ = "muscle_groups"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)

    catalog_entries = relationship(
        "ExerciseCatalog",
        secondary=exercise_muscle_map,
        back_populates="muscles"
    )

class ExerciseCatalog(SystemBase):
    __tablename__ = "exercise_catalog"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=False)
    equipment_name = Column(Integer, ForeignKey("equipment.name"))
    weight = Column(Float)
    measured_by = Column(String, default="reps")

    equipment = relationship("Equipment", back_populates="catalog_entries")
    muscles = relationship(
        "MuscleGroup",
        secondary=exercise_muscle_map,
        back_populates="catalog_entries"
    )