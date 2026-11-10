from datetime import date

from sqlmodel import Session, select

from app.models.award_category import AwardCategory
from app.models.nomination import Nomination
from app.models.volunteer_hours import VolunteerHours


def login(client, username: str) -> None:
    response = client.post(
        "/login",
        data={"username": username, "password": "test-password"},
        follow_redirects=False,
    )
    assert response.status_code == 303
    assert "access_token" in client.cookies


def test_health_and_users_api_return_expected_shapes(client, seeded_data):
    health = client.get("/health")
    assert health.status_code == 200
    assert health.json() == {"ok": True}

    response = client.get("/api/users")
    assert response.status_code == 200
    users = response.json()
    assert {user["username"] for user in users} == {"bob", "teacher", "admin"}
    assert all("password" not in user for user in users)


def test_student_hours_submission_and_teacher_approval(
    client, seeded_data, test_engine
):
    login(client, "bob")
    submitted = client.post(
        "/app/hours",
        data={
            "entry_date": "2026-10-01",
            "hours": "2.5",
            "description": "Community garden",
            "supervisor": "Garden Club",
        },
    )
    assert submitted.status_code == 200
    assert "Hours submitted successfully" in submitted.text
    assert "Pending teacher verification" in submitted.text

    login(client, "teacher")
    pending = client.get("/teacher/hours")
    assert pending.status_code == 200
    assert "bob" in pending.text
    assert "Community garden" in pending.text

    with Session(test_engine) as session:
        entry = session.exec(select(VolunteerHours)).one()
        entry_id = entry.id

    reviewed = client.post(
        f"/teacher/hours/{entry_id}/review",
        data={"decision": "approve"},
        follow_redirects=False,
    )
    assert reviewed.status_code == 303

    pending_after_approval = client.get("/teacher/hours")
    assert pending_after_approval.status_code == 200
    assert "Community garden" not in pending_after_approval.text

    duplicate_review = client.post(
        f"/teacher/hours/{entry_id}/review",
        data={"decision": "approve"},
    )
    assert duplicate_review.status_code == 400
    assert "Only pending entries can be reviewed" in duplicate_review.text

    with Session(test_engine) as session:
        entry = session.get(VolunteerHours, entry_id)
        assert entry is not None
        assert entry.status == "verified"
        assert entry.hours == 2.5

    login(client, "bob")
    dashboard = client.get("/app")
    assert dashboard.status_code == 200
    assert "Verified hours" in dashboard.text
    assert "2.5 hrs" in dashboard.text
    assert "Verified" in dashboard.text


def test_rejected_hours_require_a_comment_and_do_not_count(
    client, seeded_data, test_engine
):
    login(client, "bob")
    client.post(
        "/app/hours",
        data={
            "entry_date": "2026-10-02",
            "hours": "3",
            "description": "Unconfirmed activity",
        },
    )
    with Session(test_engine) as session:
        entry_id = session.exec(select(VolunteerHours.id)).one()

    login(client, "teacher")
    missing_comment = client.post(
        f"/teacher/hours/{entry_id}/review",
        data={"decision": "reject", "comment": "   "},
    )
    assert missing_comment.status_code == 400
    assert "A comment is required" in missing_comment.text

    with Session(test_engine) as session:
        entry = session.get(VolunteerHours, entry_id)
        assert entry is not None
        assert entry.status == "pending"

    rejected = client.post(
        f"/teacher/hours/{entry_id}/review",
        data={"decision": "reject", "comment": "Please add a supervisor."},
        follow_redirects=False,
    )
    assert rejected.status_code == 303

    login(client, "bob")
    dashboard = client.get("/app")
    assert "Rejected" in dashboard.text
    assert "Please add a supervisor." in dashboard.text
    assert "0.0 hrs" in dashboard.text


def test_nomination_requires_eligibility_and_prevents_duplicates(
    client, seeded_data, test_engine
):
    with Session(test_engine) as session:
        session.add(
            VolunteerHours(
                user_id=seeded_data["bob"],
                date=date(2026, 9, 1),
                hours=19,
                description="Verified service",
                status="verified",
            )
        )
        session.commit()

    login(client, "teacher")
    ineligible = client.post(
        "/teacher/nominations",
        data={
            "student_id": seeded_data["bob"],
            "category_id": seeded_data["bronze"],
            "reason": "Good work",
        },
    )
    assert ineligible.status_code == 400
    assert "has not met" in ineligible.text

    with Session(test_engine) as session:
        entry = session.exec(select(VolunteerHours)).one()
        entry.status = "verified"
        entry.hours = 20
        session.add(entry)
        session.commit()

    submitted = client.post(
        "/teacher/nominations",
        data={
            "student_id": seeded_data["bob"],
            "category_id": seeded_data["bronze"],
            "reason": "Consistent community service",
        },
        follow_redirects=False,
    )
    assert submitted.status_code == 303
    assert "/submitted" in submitted.headers["location"]

    duplicate = client.post(
        "/teacher/nominations",
        data={
            "student_id": seeded_data["bob"],
            "category_id": seeded_data["bronze"],
            "reason": "Another nomination",
        },
    )
    assert duplicate.status_code == 400
    assert "already has a nomination" in duplicate.text


def test_approved_nomination_is_shown_as_an_award(
    client, seeded_data, test_engine
):
    with Session(test_engine) as session:
        session.add(
            VolunteerHours(
                user_id=seeded_data["bob"],
                date=date(2026, 9, 1),
                hours=20,
                description="Verified service",
                status="verified",
            )
        )
        session.commit()

    login(client, "teacher")
    submitted = client.post(
        "/teacher/nominations",
        data={
            "student_id": seeded_data["bob"],
            "category_id": seeded_data["bronze"],
            "reason": "Consistent community service",
        },
        follow_redirects=False,
    )
    assert submitted.status_code == 303
    nomination_id = submitted.headers["location"].split("/")[-2]

    login(client, "admin")
    decision = client.post(
        f"/admin/nominations/{nomination_id}/decision",
        data={"decision": "approved"},
        follow_redirects=False,
    )
    assert decision.status_code == 303

    login(client, "bob")
    dashboard = client.get("/app")
    assert dashboard.status_code == 200
    assert "Bronze Service" in dashboard.text
    assert "Awarded" in dashboard.text


def test_admin_category_management_and_reference_guard(
    client, seeded_data, test_engine
):
    login(client, "admin")
    created = client.post(
        "/admin/categories",
        data={
            "name": "Community Star",
            "description": "Outstanding local service",
            "required_hours": 10,
        },
        follow_redirects=False,
    )
    assert created.status_code == 303

    with Session(test_engine) as session:
        category = session.exec(
            select(AwardCategory).where(AwardCategory.name == "Community Star")
        ).one()
        category_id = category.id

    updated = client.post(
        f"/admin/categories/{category_id}",
        data={
            "name": "Community Star",
            "description": "Updated description",
            "required_hours": 15,
        },
        follow_redirects=False,
    )
    assert updated.status_code == 303

    with Session(test_engine) as session:
        nomination = Nomination(
            student_id=seeded_data["bob"],
            teacher_id=seeded_data["teacher"],
            category_id=seeded_data["bronze"],
            date=date(2026, 10, 1),
            reason="Consistent community service",
        )
        session.add(nomination)
        session.commit()

    blocked_delete = client.post(
        f"/admin/categories/{seeded_data['bronze']}/delete",
        follow_redirects=False,
    )
    assert blocked_delete.status_code == 303
    with Session(test_engine) as session:
        assert session.get(AwardCategory, seeded_data["bronze"]) is not None
        category = session.get(AwardCategory, category_id)
        assert category is not None
        assert category.required_hours == 15
        assert category.description == "Updated description"

    deleted = client.post(
        f"/admin/categories/{category_id}/delete",
        follow_redirects=False,
    )
    assert deleted.status_code == 303
    with Session(test_engine) as session:
        assert session.get(AwardCategory, category_id) is None


def test_student_cannot_access_teacher_workflow(client, seeded_data):
    login(client, "bob")

    response = client.get("/teacher/hours")

    assert response.status_code == 403
