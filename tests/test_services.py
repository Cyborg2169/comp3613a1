from datetime import date
from unittest.mock import Mock

import pytest

from app.models.award_category import AwardCategory
from app.models.user import User
from app.models.volunteer_hours import VolunteerHours
from app.services.award_category_service import AwardCategoryService
from app.services.nomination_service import NominationService
from app.services.volunteer_hours_service import VolunteerHoursService


def test_submit_hours_creates_pending_entry():
    repository = Mock()
    repository.create.side_effect = lambda entry: entry
    service = VolunteerHoursService(repository)

    entry = service.submit_hours(
        user_id=7,
        entry_date=date(2026, 10, 1),
        hours=2.5,
        description="Community garden",
        supervisor="Garden Club",
    )

    assert entry.user_id == 7
    assert entry.hours == 2.5
    assert entry.status == "pending"
    repository.create.assert_called_once_with(entry)


@pytest.mark.parametrize("hours", [0, -1])
def test_submit_hours_rejects_non_positive_amount(hours):
    repository = Mock()
    service = VolunteerHoursService(repository)

    with pytest.raises(ValueError, match="greater than zero"):
        service.submit_hours(7, date(2026, 10, 1), hours, "Community garden", None)

    repository.create.assert_not_called()


def test_hours_overview_counts_only_pending_and_verified_entries():
    repository = Mock()
    repository.list_by_user.return_value = [
        VolunteerHours(
            user_id=7,
            date=date(2026, 10, 1),
            hours=2.5,
            description="Verified",
            status="verified",
        ),
        VolunteerHours(
            user_id=7,
            date=date(2026, 10, 2),
            hours=3,
            description="Pending",
            status="pending",
        ),
        VolunteerHours(
            user_id=7,
            date=date(2026, 10, 3),
            hours=4,
            description="Rejected",
            status="rejected",
        ),
    ]
    service = VolunteerHoursService(repository)

    entries, verified, pending = service.get_hours_overview(7)

    assert len(entries) == 3
    assert verified == 2.5
    assert pending == 3


@pytest.mark.parametrize(
    ("decision", "comment", "expected_status"),
    [
        ("approve", None, "verified"),
        ("reject", "Not enough detail", "rejected"),
    ],
)
def test_review_hours_records_decision(decision, comment, expected_status):
    entry = VolunteerHours(
        id=11,
        user_id=7,
        date=date(2026, 10, 1),
        hours=2.5,
        description="Community garden",
        status="pending",
    )
    repository = Mock()
    repository.get_by_id.return_value = entry
    repository.update.side_effect = lambda updated: updated
    service = VolunteerHoursService(repository)

    result = service.review_hours(11, 3, decision, comment)

    assert result.status == expected_status
    assert result.reviewed_by_id == 3
    assert result.review_comment == comment
    repository.update.assert_called_once_with(entry)


def test_review_hours_rejects_second_review_after_approval():
    entry = VolunteerHours(
        id=11,
        user_id=7,
        date=date(2026, 10, 1),
        hours=2.5,
        description="Community garden",
        status="pending",
    )
    repository = Mock()
    repository.get_by_id.return_value = entry
    repository.update.side_effect = lambda updated: updated
    service = VolunteerHoursService(repository)

    service.review_hours(11, 3, "approve", None)
    with pytest.raises(ValueError, match="Only pending"):
        service.review_hours(11, 3, "approve", None)

    assert entry.status == "verified"
    repository.update.assert_called_once_with(entry)


@pytest.mark.parametrize(
    ("entry", "decision", "comment", "message"),
    [
        (None, "approve", None, "Entry not found"),
        (
            VolunteerHours(
                id=11,
                user_id=7,
                date=date(2026, 10, 1),
                hours=2,
                description="Already reviewed",
                status="verified",
            ),
            "reject",
            "Try again",
            "Only pending",
        ),
        (
            VolunteerHours(
                id=11,
                user_id=7,
                date=date(2026, 10, 1),
                hours=2,
                description="Community garden",
                status="pending",
            ),
            "defer",
            None,
            "Decision must be",
        ),
        (
            VolunteerHours(
                id=11,
                user_id=7,
                date=date(2026, 10, 1),
                hours=2,
                description="Community garden",
                status="pending",
            ),
            "reject",
            "   ",
            "comment is required",
        ),
    ],
)
def test_review_hours_rejects_invalid_review(entry, decision, comment, message):
    repository = Mock()
    repository.get_by_id.return_value = entry
    service = VolunteerHoursService(repository)

    with pytest.raises(ValueError, match=message):
        service.review_hours(11, 3, decision, comment)

    repository.update.assert_not_called()


def _nomination_repository() -> Mock:
    repository = Mock()
    repository.get_student.return_value = User(
        id=7,
        username="bob",
        email="bob@example.com",
        password="hashed",
        role="regular_user",
    )
    repository.get_category.return_value = AwardCategory(
        id=2,
        name="Bronze Service",
        description="Getting started",
        required_hours=20,
    )
    repository.get_verified_hours.return_value = 20
    repository.has_nomination.return_value = False
    repository.submit.side_effect = lambda nomination: nomination
    return repository


def test_submit_nomination_trims_reason_and_records_submission():
    repository = _nomination_repository()
    service = NominationService(repository)

    nomination = service.submit_nomination(7, 3, 2, "  Great service  ")

    assert nomination.student_id == 7
    assert nomination.teacher_id == 3
    assert nomination.category_id == 2
    assert nomination.reason == "Great service"
    assert nomination.status == "submitted"
    repository.submit.assert_called_once_with(nomination)


@pytest.mark.parametrize(
    ("verified_hours", "already_nominated", "reason", "message"),
    [
        (19, False, "Good work", "has not met"),
        (20, True, "Good work", "already has a nomination"),
        (20, False, "  ", "reason is required"),
    ],
)
def test_submit_nomination_rejects_ineligible_duplicate_or_blank_reason(
    verified_hours, already_nominated, reason, message
):
    repository = _nomination_repository()
    repository.get_verified_hours.return_value = verified_hours
    repository.has_nomination.return_value = already_nominated
    service = NominationService(repository)

    with pytest.raises(ValueError, match=message):
        service.submit_nomination(7, 3, 2, reason)

    repository.submit.assert_not_called()


def test_category_options_compare_verified_hours_to_each_threshold():
    repository = _nomination_repository()
    repository.get_verified_hours.return_value = 25
    repository.list_categories.return_value = [
        AwardCategory(
            id=2,
            name="Bronze Service",
            description="Getting started",
            required_hours=20,
        ),
        AwardCategory(
            id=3,
            name="Silver Service",
            description="Strong volunteering",
            required_hours=50,
        ),
    ]
    service = NominationService(repository)

    student, verified_hours, options = service.get_category_options(7)

    assert student.username == "bob"
    assert verified_hours == 25
    assert [(category.name, eligible) for category, eligible in options] == [
        ("Bronze Service", True),
        ("Silver Service", False),
    ]


def test_create_category_trims_fields_and_requires_positive_hours():
    repository = Mock()
    repository.get_by_name.return_value = None
    repository.create.side_effect = lambda category: category
    service = AwardCategoryService(repository)

    category = service.create_category("  Community Star ", "  Helpful  ", 10)

    assert category.name == "Community Star"
    assert category.description == "Helpful"
    assert category.required_hours == 10
    repository.create.assert_called_once_with(category)


@pytest.mark.parametrize(
    ("name", "required_hours", "existing_name", "message"),
    [
        ("  ", 10, None, "name is required"),
        ("Bronze Service", 10, "Bronze Service", "already exists"),
        ("Community Star", 0, None, "greater than zero"),
    ],
)
def test_create_category_rejects_invalid_fields(
    name, required_hours, existing_name, message
):
    repository = Mock()
    repository.get_by_name.return_value = (
        AwardCategory(
            id=1,
            name=existing_name,
            description="",
            required_hours=20,
        )
        if existing_name
        else None
    )
    service = AwardCategoryService(repository)

    with pytest.raises(ValueError, match=message):
        service.create_category(name, "Description", required_hours)

    repository.create.assert_not_called()


def test_delete_category_is_blocked_while_nominations_reference_it():
    category = AwardCategory(
        id=2,
        name="Bronze Service",
        description="Getting started",
        required_hours=20,
    )
    repository = Mock()
    repository.get_by_id.return_value = category
    repository.has_nominations.return_value = True
    service = AwardCategoryService(repository)

    with pytest.raises(ValueError, match="cannot be deleted"):
        service.delete_category(2)

    repository.delete.assert_not_called()
