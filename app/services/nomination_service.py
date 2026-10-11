from datetime import date

from sqlalchemy.exc import IntegrityError

from app.models.award_category import AwardCategory
from app.models.nomination import Nomination
from app.models.user import User
from app.repositories.nomination import NominationRepository


class NominationService:
    def __init__(self, repository: NominationRepository):
        self.repository = repository

    def submit_nomination(
        self,
        student_id: int,
        teacher_id: int,
        category_id: int,
        reason: str,
    ) -> Nomination:
        student = self.repository.get_student(student_id)
        if student is None or student.role != "regular_user":
            raise ValueError("Student account not found")
        category = self.repository.get_category(category_id)
        if category is None:
            raise ValueError("Award category not found")
        if self.repository.get_verified_hours(student_id) < category.required_hours:
            raise ValueError("Student has not met this category's verified-hour requirement")
        if self.repository.has_nomination(student_id, category_id):
            raise ValueError("This student already has a nomination for that category")
        if not reason.strip():
            raise ValueError("A reason is required")

        nomination = Nomination(
            student_id=student_id,
            teacher_id=teacher_id,
            category_id=category_id,
            date=date.today(),
            reason=reason.strip(),
            status="submitted",
        )
        try:
            return self.repository.submit(nomination)
        except IntegrityError as exc:
            raise ValueError(
                "This student already has a nomination for that category"
            ) from exc

    def list_students(
        self, query: str = ""
    ) -> list[tuple[User, float, int]]:
        return self.repository.list_students(query)

    def get_category_options(
        self, student_id: int
    ) -> tuple[User, float, list[tuple[AwardCategory, bool]]]:
        student = self.repository.get_student(student_id)
        if student is None or student.role != "regular_user":
            raise ValueError("Student account not found")
        verified_hours = self.repository.get_verified_hours(student_id)
        options = [
            (category, verified_hours >= category.required_hours)
            for category in self.repository.list_categories()
        ]
        return student, verified_hours, options

    def get_nomination_form(
        self, student_id: int, category_id: int
    ) -> tuple[User, float, AwardCategory, list[AwardCategory]]:
        student, verified_hours, options = self.get_category_options(student_id)
        category = self.repository.get_category(category_id)
        if category is None:
            raise ValueError("Award category not found")
        eligible_categories = [
            option for option, eligible in options if eligible
        ]
        eligible_category_ids = {option.id for option in eligible_categories}
        if category.id not in eligible_category_ids:
            raise ValueError("Student is not eligible for this award category")
        return student, verified_hours, category, eligible_categories

    def list_for_teacher(
        self, teacher_id: int
    ) -> list[tuple[Nomination, str, str]]:
        return self.repository.list_for_teacher(teacher_id)

    def get_submission(
        self, nomination_id: int, teacher_id: int
    ) -> tuple[Nomination, str, str] | None:
        return self.repository.get_submission(nomination_id, teacher_id)

    def review_nomination(
        self, nomination_id: int, decision: str, reviewer_id: int
    ) -> Nomination:
        if decision not in ("approved", "rejected"):
            raise ValueError("Decision must be approved or rejected")
        nomination = self.repository.record_decision(
            nomination_id, decision, reviewer_id
        )
        if nomination is None:
            raise ValueError("Nomination not found or already reviewed")
        return nomination

    def list_for_admin(self) -> list[tuple[Nomination, str, str]]:
        return self.repository.list_for_admin()

    def list_approved_for_student(
        self, student_id: int
    ) -> list[tuple[Nomination, str]]:
        return self.repository.list_approved_for_student(student_id)
