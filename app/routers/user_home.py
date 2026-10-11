from fastapi import Request
from fastapi.responses import HTMLResponse

from app.dependencies.session import SessionDep
from app.dependencies.auth import StudentDep
from app.repositories.nomination import NominationRepository
from app.repositories.volunteer_hours import VolunteerHoursRepository
from app.services.nomination_service import NominationService
from app.services.volunteer_hours_service import VolunteerHoursService
from . import router, templates


@router.get("/app", response_class=HTMLResponse)
async def user_home_view(
    request: Request,
    user: StudentDep,
    db: SessionDep,
):
    service = VolunteerHoursService(VolunteerHoursRepository(db))
    entries, verified_hours, pending_hours = service.get_hours_overview(user.id)
    awards = NominationService(
        NominationRepository(db)
    ).list_approved_for_student(user.id)
    return templates.TemplateResponse(
        request=request,
        name="my_hours.html",
        context={
            "user": user,
            "entries": entries,
            "verified_hours": verified_hours,
            "pending_hours": pending_hours,
            "progress_target": 50,
            "awards": awards,
        },
    )