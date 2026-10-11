from sqlmodel import Session, select

from app.models.volunteer_hours import VolunteerHours
from app.models.user import User


class VolunteerHoursRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, entry: VolunteerHours) -> VolunteerHours:
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_by_user(self, user_id: int) -> list[VolunteerHours]:
        statement = (
            select(VolunteerHours)
            .where(VolunteerHours.user_id == user_id)
            .order_by(VolunteerHours.date.desc(), VolunteerHours.id.desc())
        )
        return list(self.db.exec(statement).all())

    def get_by_id(self, entry_id: int) -> VolunteerHours | None:
        return self.db.get(VolunteerHours, entry_id)

    def update(self, entry: VolunteerHours) -> VolunteerHours:
        self.db.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def list_pending(self, query: str = "") -> list[tuple[VolunteerHours, str]]:
        statement = (
            select(VolunteerHours, User.username)
            .join(User, User.id == VolunteerHours.user_id)
            .where(VolunteerHours.status == "pending")
        )
        if query.strip():
            statement = statement.where(User.username.ilike(f"%{query.strip()}%"))
        statement = statement.order_by(
            VolunteerHours.date.asc(), VolunteerHours.id.asc()
        )
        return [
            (entry, username)
            for entry, username in self.db.exec(statement).all()
        ]

    def get_review_details(
        self, entry_id: int
    ) -> tuple[VolunteerHours, str] | None:
        statement = (
            select(VolunteerHours, User.username)
            .join(User, User.id == VolunteerHours.user_id)
            .where(VolunteerHours.id == entry_id)
        )
        result = self.db.exec(statement).one_or_none()
        if result is None:
            return None
        entry, username = result
        return entry, username
