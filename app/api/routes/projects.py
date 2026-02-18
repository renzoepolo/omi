from fastapi import APIRouter, Depends

from app.api.deps import get_project_membership
from app.models import UserProject

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/current")
def current_project_context(membership: UserProject = Depends(get_project_membership)) -> dict:
    return {
        "project_id": membership.project_id,
        "role": membership.role.value,
        "user_id": membership.user_id,
    }
