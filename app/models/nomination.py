from datetime import date
from typing import Optional

from sqlalchemy import UniqueConstraint
from sqlmodel import Field, SQLModel


class Nomination(SQLModel, table=True):
    __table_args__ = (
        UniqueConstraint(
            "student_id",
            "category_id",
            name="uq_nomination_student_category",
        ),
    )

    id: Optional[int] = Field(default=None, primary_key=True)

    # STUDENT SNIPPET START
    student_id: int = Field(foreign_key="user.id")
    teacher_id: int = Field(foreign_key="user.id")
    category_id: int = Field(foreign_key="awardcategory.id")
    date: date
    reason: str
    status: str = "submitted"
    # STUDENT SNIPPET END

    reviewer_id: Optional[int] = Field(default=None, foreign_key="user.id")
