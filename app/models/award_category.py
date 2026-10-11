from typing import Optional

from sqlmodel import Field, SQLModel


class AwardCategory(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str = ""

    # STUDENT SNIPPET START
    name: str = Field(unique=True, index=True)
    required_hours: int = Field(gt=0)
    # STUDENT SNIPPET END
