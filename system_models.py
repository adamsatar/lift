from sqlalchemy import MetaData
from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List

system_metadata = MetaData()

class SystemBase(SQLModel):
    metadata = system_metadata

class ExerciseMuscleLink(SystemBase, table=True):
    __tablename__ = "exercise_muscle_link"

    exercise_id: int = Field(foreign_key="exercise_catalog.id", primary_key=True)
    muscle_group_id: int = Field(foreign_key="muscle_groups.id", primary_key=True)

    exercise: Optional["ExerciseCatalog"] = Relationship(back_populates="muscle_links")
    muscle_group: Optional["MuscleGroup"] = Relationship(back_populates="exercise_links")


class Equipment(SystemBase, table=True):
    __tablename__ = "equipment"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    default_weight: float = 0.0
    track_weight: bool = True
    has_resistance_levels: bool = False

    catalog_entries: List["ExerciseCatalog"] = Relationship(back_populates="equipment")


class MuscleGroup(SystemBase, table=True):
    __tablename__ = "muscle_groups"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str

    catalog_entries: List["ExerciseCatalog"] = Relationship(
        back_populates="muscles", link_model=ExerciseMuscleLink
    )
    exercise_links: List["ExerciseMuscleLink"] = Relationship(back_populates="muscle_group")


class ExerciseCatalog(SystemBase, table=True):
    __tablename__ = "exercise_catalog"
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    equipment_id: Optional[int] = Field(foreign_key="equipment.id")
    weight: Optional[float]
    measured_by: str = "reps"

    equipment: Optional[Equipment] = Relationship(back_populates="catalog_entries")
    muscles: List[MuscleGroup] = Relationship(
        back_populates="catalog_entries", link_model=ExerciseMuscleLink
    )
    muscle_links: List[ExerciseMuscleLink] = Relationship(back_populates="exercise")


def create_all_system_tables(engine):
    system_metadata.create_all(engine)