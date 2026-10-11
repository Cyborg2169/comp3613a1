from datetime import date
from typing import Optional

from sqlmodel import Field, SQLModel


class VolunteerHours(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # STUDENT SNIPPET START
        
    user_id: int = Field(foreign_key="user.id")
    date: date
    hours: float
    description: str
    status: str = "pending"
    supervisor: Optional[str] = None

    # STUDENT SNIPPET 2 START
    review_comment: Optional[str] = None
    # STUDENT SNIPPET 2 END

    # STUDENT SNIPPET 3 START
    reviewed_by_id: Optional[int] = Field(default=None, foreign_key="user.id")
    # STUDENT SNIPPET 3 END
    
    # STUDENT SNIPPET END
