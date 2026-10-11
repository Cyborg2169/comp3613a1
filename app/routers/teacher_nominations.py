from fastapi import Form, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from app.dependencies.auth import TeacherDep
from app.dependencies.session import SessionDep
from app.repositories.nomination import NominationRepository
from app.services.nomination_service import NominationService
from . import router, templates


@router.get(
    "/teacher/nominations/{nomination_id}/submitted",
    response_class=HTMLResponse,
    name="nomination_submitted_view",
)
async def nomination_submitted_view(
    request: Request,
    nomination_id: int,
    teacher: TeacherDep,
    db: SessionDep,
):
    service = NominationService(NominationRepository(db))
    submission = service.get_submission(nomination_id, teacher.id)
    if submission is None:
        raise HTTPException(status_code=404, detail="Nomination not found")
    nomination, student_username, category_name = submission
    nominations = service.list_for_teacher(teacher.id)
    return templates.TemplateResponse(
        request=request,
        name="nomination_submitted.html",
        context={
            "user": teacher,
            "nomination": nomination,
            "student_username": student_username,
            "category_name": category_name,
            "nominations": nominations,
        },
    )


@router.get(
    "/teacher/nominations",
    response_class=HTMLResponse,
    name="teacher_nominations_view",
)
async def teacher_nominations_view(
    request: Request,
    teacher: TeacherDep,
    db: SessionDep,
    query: str = "",
):
    service = NominationService(NominationRepository(db))
    students = service.list_students(query)
    return templates.TemplateResponse(
        request=request,
        name="teacher_nominations.html",
        context={"user": teacher, "students": students, "query": query},
    )


@router.get(
    "/teacher/nominations/category/{student_id}",
    response_class=HTMLResponse,
    name="nomination_category_view",
)
async def nomination_category_view(
    request: Request,
    student_id: int,
    teacher: TeacherDep,
    db: SessionDep,
):
    service = NominationService(NominationRepository(db))
    try:
        student, verified_hours, category_options = service.get_category_options(
            student_id
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request=request,
        name="select_award_category.html",
        context={
            "user": teacher,
            "student": student,
            "verified_hours": verified_hours,
            "category_options": category_options,
            "has_eligible": any(eligible for _, eligible in category_options),
            "error": None,
        },
    )


@router.post(
    "/teacher/nominations/choose-category",
    name="nomination_choose_category_action",
)
async def nomination_choose_category_action(
    request: Request,
    teacher: TeacherDep,
    db: SessionDep,
    student_id: int = Form(...),
    category_id: int = Form(...),
):
    service = NominationService(NominationRepository(db))
    try:
        service.get_nomination_form(student_id, category_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(
        url=(
            f"/teacher/nominations/new?student_id={student_id}"
            f"&category_id={category_id}"
        ),
        status_code=303,
    )


@router.get(
    "/teacher/nominations/new",
    response_class=HTMLResponse,
    name="nomination_form_view",
)
async def nomination_form_view(
    request: Request,
    student_id: int,
    category_id: int,
    teacher: TeacherDep,
    db: SessionDep,
):
    service = NominationService(NominationRepository(db))
    try:
        student, verified_hours, category, eligible_categories = (
            service.get_nomination_form(student_id, category_id)
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return templates.TemplateResponse(
        request=request,
        name="nomination_form.html",
        context={
            "user": teacher,
            "student": student,
            "verified_hours": verified_hours,
            "category": category,
            "eligible_categories": eligible_categories,
            "error": None,
        },
    )


@router.post(
    "/teacher/nominations",
    response_class=HTMLResponse,
    name="nomination_submit_action",
)
async def nomination_submit_action(
    request: Request,
    teacher: TeacherDep,
    db: SessionDep,
    student_id: int = Form(...),
    category_id: int = Form(...),
    reason: str = Form(...),
):
    # STUDENT SNIPPET START
    service = NominationService(NominationRepository(db))
    try:
        nomination = service.submit_nomination(
            student_id=student_id,
            teacher_id=teacher.id,
            category_id=category_id,
            reason=reason,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return RedirectResponse(
        url=f"/teacher/nominations/{nomination.id}/submitted",
        status_code=303,
    )
    # STUDENT SNIPPET END
