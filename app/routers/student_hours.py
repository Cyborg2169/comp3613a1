from datetime import date

from fastapi import Form, Request
from fastapi.responses import HTMLResponse

from app.dependencies.auth import StudentDep
from app.dependencies.session import SessionDep
from app.repositories.volunteer_hours import VolunteerHoursRepository
from app.services.volunteer_hours_service import VolunteerHoursService
from . import router, templates


@router.get("/app/hours/new", response_class=HTMLResponse, name="log_volunteer_hours_view")
async def log_volunteer_hours_view(request: Request, user: StudentDep):
    return templates.TemplateResponse(
        request=request,
        name="log_hours.html",
        context={"user": user},
    )


@router.post("/app/hours", name="submit_volunteer_hours")
async def submit_volunteer_hours(
    request: Request,
    user: StudentDep,
    db: SessionDep,
    entry_date: date = Form(...),
    hours: float = Form(..., gt=0),
    description: str = Form(...),
    supervisor: str | None = Form(None),
):
    # STUDENT SNIPPET START
    service = VolunteerHoursService(VolunteerHoursRepository(db))
    entry = service.submit_hours(
        user_id=user.id,
        entry_date=entry_date,
        hours=hours,
        description=description,
        supervisor=supervisor,
    )
    return templates.TemplateResponse(
        request=request,
        name="hours_submitted.html",
        context={"user": user, "entry": entry},
    )
    # STUDENT SNIPPET END
