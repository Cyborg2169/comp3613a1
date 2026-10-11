"""Database table models.

Import every table model here so ``SQLModel.metadata.create_all`` sees them.
"""

from app.models.user import User
from app.models.volunteer_hours import VolunteerHours
from app.models.award_category import AwardCategory
from app.models.nomination import Nomination

__all__ = ["User", "VolunteerHours", "AwardCategory", "Nomination"]
