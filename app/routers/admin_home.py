from fastapi.responses import RedirectResponse

from app.dependencies.auth import AdminDep
from . import router


@router.get("/admin", name="admin_home_view")
async def admin_home_view(
    user: AdminDep,
):
    return RedirectResponse(url="/admin/categories", status_code=303)
