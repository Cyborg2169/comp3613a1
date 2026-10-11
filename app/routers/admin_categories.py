from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import AdminDep
from app.dependencies.session import SessionDep
from app.repositories.award_category import AwardCategoryRepository
from app.services.award_category_service import AwardCategoryService
from app.utilities.flash import flash
from . import router, templates


def _category_service(db: SessionDep) -> AwardCategoryService:
    return AwardCategoryService(AwardCategoryRepository(db))


@router.get(
    "/admin/categories",
    response_class=HTMLResponse,
    name="admin_categories_view",
)
async def admin_categories_view(
    request: Request,
    admin: AdminDep,
    db: SessionDep,
):
    service = _category_service(db)
    return templates.TemplateResponse(
        request=request,
        name="admin_categories.html",
        context={"user": admin, "categories": service.list_categories()},
    )


@router.get(
    "/admin/categories/new",
    response_class=HTMLResponse,
    name="new_award_category_view",
)
async def new_award_category_view(
    request: Request,
    admin: AdminDep,
):
    return templates.TemplateResponse(
        request=request,
        name="award_category_form.html",
        context={
            "user": admin,
            "category_id": None,
            "name": "",
            "description": "",
            "required_hours": "",
            "error": None,
        },
    )


@router.post(
    "/admin/categories",
    response_class=HTMLResponse,
    name="create_award_category_action",
)
async def create_award_category_action(
    request: Request,
    admin: AdminDep,
    db: SessionDep,
    name: str = Form(...),
    description: str = Form(""),
    required_hours: int = Form(...),
):
    service = _category_service(db)
    try:
        service.create_category(name, description, required_hours)
    except ValueError as exc:
        return templates.TemplateResponse(
            request=request,
            name="award_category_form.html",
            status_code=400,
            context={
                "user": admin,
                "category_id": None,
                "name": name,
                "description": description,
                "required_hours": required_hours,
                "error": str(exc),
            },
        )
    flash(request, "Award category created.", "success")
    return RedirectResponse(url="/admin/categories", status_code=303)


@router.get(
    "/admin/categories/{category_id}/edit",
    response_class=HTMLResponse,
    name="edit_award_category_view",
)
async def edit_award_category_view(
    request: Request,
    category_id: int,
    admin: AdminDep,
    db: SessionDep,
):
    category = _category_service(db).get_category(category_id)
    if category is None:
        raise HTTPException(status_code=404, detail="Award category not found")
    return templates.TemplateResponse(
        request=request,
        name="award_category_form.html",
        context={
            "user": admin,
            "category_id": category.id,
            "name": category.name,
            "description": category.description,
            "required_hours": category.required_hours,
            "error": None,
        },
    )


@router.post(
    "/admin/categories/{category_id}",
    response_class=HTMLResponse,
    name="update_award_category_action",
)
async def update_award_category_action(
    request: Request,
    category_id: int,
    admin: AdminDep,
    db: SessionDep,
    name: str = Form(...),
    description: str = Form(""),
    required_hours: int = Form(...),
):
    service = _category_service(db)
    try:
        service.update_category(category_id, name, description, required_hours)
    except ValueError as exc:
        category = service.get_category(category_id)
        if category is None:
            raise HTTPException(status_code=404, detail=str(exc)) from exc
        return templates.TemplateResponse(
            request=request,
            name="award_category_form.html",
            status_code=400,
            context={
                "user": admin,
                "category_id": category_id,
                "name": name,
                "description": description,
                "required_hours": required_hours,
                "error": str(exc),
            },
        )
    flash(request, "Award category updated.", "success")
    return RedirectResponse(url="/admin/categories", status_code=303)


@router.post(
    "/admin/categories/{category_id}/delete",
    name="delete_award_category_action",
)
async def delete_award_category_action(
    request: Request,
    category_id: int,
    admin: AdminDep,
    db: SessionDep,
):
    service = _category_service(db)
    if service.get_category(category_id) is None:
        raise HTTPException(status_code=404, detail="Award category not found")
    try:
        service.delete_category(category_id)
    except ValueError as exc:
        flash(request, str(exc), "danger")
    else:
        flash(request, "Award category deleted.", "success")
    return RedirectResponse(url="/admin/categories", status_code=303)
