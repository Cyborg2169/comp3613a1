from fastapi import Form, Request
from fastapi.responses import RedirectResponse

from app.dependencies.auth import AdminDep
from app.dependencies.session import SessionDep
from app.repositories.nomination import NominationRepository
from app.services.nomination_service import NominationService
from app.utilities.flash import flash
from . import router, templates


def _nomination_service(db: SessionDep) -> NominationService:
    return NominationService(NominationRepository(db))


@router.get("/admin/nominations", name="admin_nominations_view")
async def admin_nominations_view(
    request: Request,
    admin: AdminDep,
    db: SessionDep,
):
    return templates.TemplateResponse(
        request=request,
        name="admin_nominations.html",
        context={
            "user": admin,
            "nominations": _nomination_service(db).list_for_admin(),
        },
    )


@router.post(
    "/admin/nominations/{nomination_id}/decision",
    name="admin_nomination_decision_action",
)
async def admin_nomination_decision_action(
    request: Request,
    nomination_id: int,
    admin: AdminDep,
    db: SessionDep,
    decision: str = Form(...),
):
    try:
        _nomination_service(db).review_nomination(
            nomination_id, decision, admin.id
        )
    except ValueError as exc:
        flash(request, str(exc), "danger")
    else:
        flash(request, f"Nomination {decision}.", "success")
    return RedirectResponse(url="/admin/nominations", status_code=303)
