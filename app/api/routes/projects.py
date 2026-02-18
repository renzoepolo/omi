from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, get_project_membership
from app.core.database import get_db
from app.models import Project, User, UserProject

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("")
def list_projects(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[dict]:
    memberships = db.scalars(
        select(UserProject)
        .where(UserProject.user_id == current_user.id)
        .order_by(UserProject.project_id.asc())
    ).all()
    project_ids = [m.project_id for m in memberships]
    if not project_ids:
        return []
    projects = db.scalars(select(Project).where(Project.id.in_(project_ids))).all()
    projects_map = {p.id: p for p in projects}
    return [
        {
            "id": m.project_id,
            "name": projects_map[m.project_id].name,
            "role": m.role.value,
            "center": [-77.0428, -12.0464],
            "zoom": 13,
        }
        for m in memberships
        if m.project_id in projects_map
    ]


@router.get("/current")
def current_project_context(
    membership: UserProject = Depends(get_project_membership),
) -> dict:
    return {
        "project_id": membership.project_id,
        "role": membership.role.value,
        "user_id": membership.user_id,
    }
