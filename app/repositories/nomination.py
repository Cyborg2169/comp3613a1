from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, func, select

from app.models.award_category import AwardCategory
from app.models.nomination import Nomination
from app.models.user import User
from app.models.volunteer_hours import VolunteerHours


class NominationRepository:
    def __init__(self, db: Session):
        self.db = db

    def submit(self, nomination: Nomination) -> Nomination:
        try:
            self.db.add(nomination)
            self.db.commit()
            self.db.refresh(nomination)
            return nomination
        except IntegrityError:
            self.db.rollback()
            raise

    def list_students(
        self, query: str = ""
    ) -> list[tuple[User, float, int]]:
        hours = (
            select(
                VolunteerHours.user_id.label("student_id"),
                func.sum(VolunteerHours.hours).label("verified_hours"),
            )
            .where(VolunteerHours.status == "verified")
            .group_by(VolunteerHours.user_id)
            .subquery()
        )
        nominations = (
            select(
                Nomination.student_id.label("student_id"),
                func.count(Nomination.id).label("nomination_count"),
            )
            .group_by(Nomination.student_id)
            .subquery()
        )
        statement = (
            select(
                User,
                func.coalesce(hours.c.verified_hours, 0.0),
                func.coalesce(nominations.c.nomination_count, 0),
            )
            .outerjoin(hours, hours.c.student_id == User.id)
            .outerjoin(nominations, nominations.c.student_id == User.id)
            .where(User.role == "regular_user")
        )
        if query.strip():
            statement = statement.where(User.username.ilike(f"%{query.strip()}%"))
        statement = statement.order_by(User.username)
        return [
            (student, float(verified_hours), int(nomination_count))
            for student, verified_hours, nomination_count in self.db.exec(statement).all()
        ]

    def get_student(self, student_id: int) -> User | None:
        return self.db.get(User, student_id)

    def get_category(self, category_id: int) -> AwardCategory | None:
        return self.db.get(AwardCategory, category_id)

    def list_categories(self) -> list[AwardCategory]:
        statement = select(AwardCategory).order_by(
            AwardCategory.required_hours.desc(), AwardCategory.name
        )
        return list(self.db.exec(statement).all())

    def get_verified_hours(self, student_id: int) -> float:
        statement = select(
            func.coalesce(func.sum(VolunteerHours.hours), 0.0)
        ).where(
            VolunteerHours.user_id == student_id,
            VolunteerHours.status == "verified",
        )
        return float(self.db.exec(statement).one())

    def has_nomination(self, student_id: int, category_id: int) -> bool:
        statement = select(Nomination.id).where(
            Nomination.student_id == student_id,
            Nomination.category_id == category_id,
        )
        return self.db.exec(statement).first() is not None

    def list_for_teacher(
        self, teacher_id: int
    ) -> list[tuple[Nomination, str, str]]:
        statement = (
            select(Nomination, User.username, AwardCategory.name)
            .join(User, User.id == Nomination.student_id)
            .join(AwardCategory, AwardCategory.id == Nomination.category_id)
            .where(Nomination.teacher_id == teacher_id)
            .order_by(Nomination.date.desc(), Nomination.id.desc())
        )
        return list(self.db.exec(statement).all())

    def get_submission(
        self, nomination_id: int, teacher_id: int
    ) -> tuple[Nomination, str, str] | None:
        statement = (
            select(Nomination, User.username, AwardCategory.name)
            .join(User, User.id == Nomination.student_id)
            .join(AwardCategory, AwardCategory.id == Nomination.category_id)
            .where(
                Nomination.id == nomination_id,
                Nomination.teacher_id == teacher_id,
            )
        )
        return self.db.exec(statement).one_or_none()
