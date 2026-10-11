from datetime import date

from app.models.volunteer_hours import VolunteerHours
from app.repositories.volunteer_hours import VolunteerHoursRepository


class VolunteerHoursService:
    def __init__(self, repository: VolunteerHoursRepository):
        self.repository = repository

    def submit_hours(
        self,
        user_id: int,
        entry_date: date,
        hours: float,
        description: str,
        supervisor: str | None,
    ) -> VolunteerHours:
        # STUDENT SNIPPET START
        # Complete this application method using the repository.
        if hours <= 0:
            raise ValueError("Hours must be greater than zero")
        entry = VolunteerHours(
            user_id=user_id,
            date=entry_date,
            hours=hours,
            description=description,
            supervisor=supervisor,
            status="pending",
        )
        return self.repository.create(entry)
        # STUDENT SNIPPET END

    def get_hours_overview(
        self, user_id: int
    ) -> tuple[list[VolunteerHours], float, float]:
        entries = self.repository.list_by_user(user_id)
        verified_hours = sum(
            entry.hours for entry in entries if entry.status == "verified"
        )
        pending_hours = sum(
            entry.hours for entry in entries if entry.status == "pending"
        )
        return entries, verified_hours, pending_hours

    def review_hours(
        self,
        entry_id: int,
        teacher_id: int,
        decision: str,
        comment: str | None,
    ) -> VolunteerHours:
        # STUDENT SNIPPET START
        # Complete the review rules and delegate persistence to the repository.
        entry = self.repository.get_by_id(entry_id)
        if entry is None:
            raise ValueError("Entry not found")
        if entry.status != "pending":
            raise ValueError("Only pending entries can be reviewed")
        if decision not in ("approve", "reject"):
            raise ValueError("Decision must be approve or reject")
        if decision == "reject" and not (comment and comment.strip()):
            raise ValueError("A comment is required when rejecting")

        entry.status = "verified" if decision == "approve" else "rejected"
        entry.review_comment = comment.strip() if comment else None
        entry.reviewed_by_id = teacher_id
        return self.repository.update(entry)
        # STUDENT SNIPPET END

    def list_pending(self, query: str = "") -> list[tuple[VolunteerHours, str]]:
        return self.repository.list_pending(query)

    def get_review_details(
        self, entry_id: int
    ) -> tuple[VolunteerHours, str] | None:
        return self.repository.get_review_details(entry_id)
