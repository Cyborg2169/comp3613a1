from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import TeacherDep
from app.dependencies.session import SessionDep
from app.repositories.volunteer_hours import VolunteerHoursRepository
from app.services.volunteer_hours_service import VolunteerHoursService
from . import router, templates


@router.get(
    "/teacher/hours",
    response_class=HTMLResponse,
    name="teacher_pending_hours_view",
)
async def teacher_pending_hours_view(
    request: Request,
    teacher: TeacherDep,
    db: SessionDep,
    query: str = "",
):
    service = VolunteerHoursService(VolunteerHoursRepository(db))
    entries = service.list_pending(query)
    return templates.TemplateResponse(
        request=request,
        name="teacher_pending_hours.html",
        context={"user": teacher, "entries": entries, "query": query},
    )


@router.get(
    "/teacher/hours/{entry_id}",
    response_class=HTMLResponse,
    name="review_entry_view",
)
async def review_entry_view(
    request: Request,
    entry_id: int,
    teacher: TeacherDep,
    db: SessionDep,
):
    service = VolunteerHoursService(VolunteerHoursRepository(db))
    details = service.get_review_details(entry_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Volunteer-hour entry not found")
    entry, student_username = details
    return templates.TemplateResponse(
        request=request,
        name="review_hours.html",
        context={
            "user": teacher,
            "entry": entry,
            "student_username": student_username,
            "error": None,
            "comment": None,
        },
    )


@router.post(
    "/teacher/hours/{entry_id}/review",
    response_class=HTMLResponse,
    name="review_volunteer_hours",
)
async def review_volunteer_hours(
    request: Request,
    teacher: TeacherDep,
    db: SessionDep,
    entry_id: int,
    decision: str = Form(...),
    comment: str | None = Form(None),
):
    # STUDENT SNIPPET START
    service = VolunteerHoursService(VolunteerHoursRepository(db))
    try:
        service.review_hours(
            entry_id=entry_id,
            teacher_id=teacher.id,
            decision=decision,
            comment=comment,
        )
    except ValueError as exc:
        details = service.get_review_details(entry_id)
        if details is None:
            raise HTTPException(
                status_code=404, detail="Volunteer-hour entry not found"
            ) from exc
        entry, student_username = details
        return templates.TemplateResponse(
            request=request,
            name="review_hours.html",
            context={
                "user": teacher,
                "entry": entry,
                "student_username": student_username,
                "error": str(exc),
                "comment": comment,
            },
            status_code=400,
        )
    return RedirectResponse(url=f"/teacher/hours/{entry_id}/result", status_code=303)
    # STUDENT SNIPPET END


@router.get(
    "/teacher/hours/{entry_id}/result",
    response_class=HTMLResponse,
    name="teacher_decision_result_view",
)
async def teacher_decision_result_view(
    request: Request,
    entry_id: int,
    teacher: TeacherDep,
    db: SessionDep,
):
    service = VolunteerHoursService(VolunteerHoursRepository(db))
    details = service.get_review_details(entry_id)
    if details is None:
        raise HTTPException(status_code=404, detail="Volunteer-hour entry not found")
    entry, student_username = details
    pending_entries = service.list_pending()
    return templates.TemplateResponse(
        request=request,
        name="teacher_decision_result.html",
        context={
            "user": teacher,
            "entry": entry,
            "student_username": student_username,
            "pending_entries": pending_entries,
        },
    )
