from urllib.parse import quote

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.deps import get_admin_membership, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.security import get_password_hash
from app.models import (
    AdminAuditLog,
    FormFieldDefinition,
    Layer,
    LayerType,
    Project,
    ProjectLayer,
    ProjectRole,
    User,
    UserProject,
)
from app.schemas.admin import (
    FormFieldDefinitionPayload,
    LayerCreate,
    LayerUpdate,
    ProjectCreate,
    ProjectLayerAttach,
    ProjectUpdate,
    UserCreate,
    UserProjectAssign,
    UserUpdate,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _normalized_project_name(value: str) -> str:
    return value.strip()


def _project_name_exists(db: Session, name: str, exclude_project_id: int | None = None) -> bool:
    normalized = _normalized_project_name(name)
    stmt = select(Project).where(func.lower(Project.name) == normalized.lower())
    if exclude_project_id is not None:
        stmt = stmt.where(Project.id != exclude_project_id)
    return db.scalar(stmt) is not None


def _is_super_admin(membership: UserProject) -> bool:
    return membership.role == ProjectRole.SUPER_ADMIN


def _ensure_project_scope(membership: UserProject, project_id: int) -> None:
    if _is_super_admin(membership):
        return
    if membership.project_id != project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ProjectAdmin can only manage their own project",
        )


def _user_in_project(db: Session, user_id: int, project_id: int) -> bool:
    return (
        db.scalar(
            select(UserProject).where(UserProject.user_id == user_id, UserProject.project_id == project_id)
        )
        is not None
    )


def _ensure_project_admin_can_manage_user(db: Session, membership: UserProject, user_id: int) -> None:
    if _is_super_admin(membership):
        return
    if not _user_in_project(db, user_id, membership.project_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="ProjectAdmin can only manage users in their own project",
        )


def _audit(
    db: Session,
    request: Request,
    actor_user_id: int,
    action: str,
    target_type: str,
    target_id: str,
    project_id: int | None,
    details: dict | None = None,
) -> None:
    db.add(
        AdminAuditLog(
            actor_user_id=actor_user_id,
            action=action,
            target_type=target_type,
            target_id=target_id,
            project_id=project_id,
            ip_address=(request.client.host if request.client else None),
            user_agent=request.headers.get("user-agent"),
            details=details or {},
        )
    )


def _fetch_geoserver_json(path: str) -> dict:
    base_url = settings.geoserver_url.rstrip("/")
    if not base_url:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="GeoServer URL is not configured")

    try:
        with httpx.Client(timeout=settings.geoserver_timeout_seconds) as client:
            response = client.get(
                f"{base_url}{path}",
                auth=(settings.geoserver_user, settings.geoserver_password),
                headers={"Accept": "application/json"},
            )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"GeoServer is not reachable: {exc}",
        ) from exc

    if response.status_code >= 400:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"GeoServer error {response.status_code}",
        )

    try:
        return response.json()
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="GeoServer returned invalid JSON",
        ) from exc


def _to_list(value) -> list[dict]:
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    if isinstance(value, dict):
        return [value]
    return []


def _extract_collection(payload: dict, root_key: str, item_key: str) -> list[dict]:
    root = payload.get(root_key, {})
    if not isinstance(root, dict):
        return []
    return _to_list(root.get(item_key))


@router.get("/geoserver/workspaces")
def admin_geoserver_workspaces(
    admin_membership: UserProject = Depends(get_admin_membership),
) -> list[dict]:
    _ = admin_membership
    payload = _fetch_geoserver_json("/rest/workspaces.json")
    rows = _extract_collection(payload, "workspaces", "workspace")
    out = []
    for row in rows:
        name = row.get("name")
        if name:
            out.append({"name": name})
    return out


@router.get("/geoserver/workspaces/{workspace}/layers")
def admin_geoserver_workspace_layers(
    workspace: str,
    admin_membership: UserProject = Depends(get_admin_membership),
) -> list[dict]:
    _ = admin_membership
    ws = quote(workspace, safe="")
    payload = _fetch_geoserver_json(f"/rest/workspaces/{ws}/layers.json")
    rows = _extract_collection(payload, "layers", "layer")
    out = []
    for row in rows:
        name = row.get("name")
        if name:
            out.append({"name": name.split(":")[-1]})
    return out


@router.get("/geoserver/workspaces/{workspace}/styles")
def admin_geoserver_workspace_styles(
    workspace: str,
    admin_membership: UserProject = Depends(get_admin_membership),
) -> list[dict]:
    _ = admin_membership
    ws = quote(workspace, safe="")
    payload = _fetch_geoserver_json(f"/rest/workspaces/{ws}/styles.json")
    rows = _extract_collection(payload, "styles", "style")
    out = []
    for row in rows:
        name = row.get("name")
        if name:
            out.append({"name": name})
    return out


@router.get("/geoserver/workspaces/{workspace}/layers/{layer_name}/styles")
def admin_geoserver_layer_styles(
    workspace: str,
    layer_name: str,
    admin_membership: UserProject = Depends(get_admin_membership),
) -> list[dict]:
    _ = admin_membership
    ws = quote(workspace, safe="")
    layer = quote(layer_name, safe="")
    payload = _fetch_geoserver_json(f"/rest/layers/{ws}:{layer}.json")
    layer_payload = payload.get("layer", {})
    if not isinstance(layer_payload, dict):
        return []

    styles_payload = layer_payload.get("styles", {})
    rows = _to_list(styles_payload.get("style")) if isinstance(styles_payload, dict) else []
    default_style = layer_payload.get("defaultStyle", {})
    names = []
    if default_style.get("name"):
        names.append(default_style["name"])
    for row in rows:
        name = row.get("name")
        if name and name not in names:
            names.append(name)
    return [{"name": name} for name in names]


@router.get("/projects")
def admin_list_projects(
    db: Session = Depends(get_db),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> list[dict]:
    if _is_super_admin(admin_membership):
        projects = db.scalars(select(Project).order_by(Project.id.asc())).all()
    else:
        projects = db.scalars(select(Project).where(Project.id == admin_membership.project_id)).all()

    out = []
    for project in projects:
        layer_rows = db.scalars(
            select(ProjectLayer).where(ProjectLayer.project_id == project.id).order_by(ProjectLayer.id.asc())
        ).all()
        form_fields = db.scalars(
            select(FormFieldDefinition)
            .where(FormFieldDefinition.project_id == project.id)
            .order_by(FormFieldDefinition.order_index.asc(), FormFieldDefinition.id.asc())
        ).all()
        out.append(
            {
                "id": project.id,
                "name": project.name,
                "description": project.description,
                "default_map_center": [project.default_center_lng or -77.0428, project.default_center_lat or -12.0464],
                "default_zoom": project.default_zoom,
                "default_base_layers": [
                    {
                        "layer_id": row.layer_id,
                        "available_override": row.available_override,
                        "visible_override": row.visible_override,
                        "z_index_override": row.z_index_override,
                        "style_name": row.layer.style_name if row.layer else None,
                    }
                    for row in layer_rows
                ],
                "form_configuration": [
                    {
                        "id": field.id,
                        "field_key": field.field_key,
                        "label": field.label,
                        "field_type": field.field_type,
                        "required": field.required,
                        "order_index": field.order_index,
                        "config": field.config,
                    }
                    for field in form_fields
                ],
            }
        )
    return out


@router.post("/projects", status_code=status.HTTP_201_CREATED)
def admin_create_project(
    payload: ProjectCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    if not _is_super_admin(admin_membership):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SuperAdmin can create projects")

    normalized_name = _normalized_project_name(payload.name)
    if _project_name_exists(db, normalized_name):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project name already exists")

    project = Project(
        name=normalized_name,
        description=payload.description,
        default_center_lng=payload.default_map_center[0],
        default_center_lat=payload.default_map_center[1],
        default_zoom=payload.default_zoom,
    )
    db.add(project)
    db.flush()

    _audit(
        db,
        request,
        current_user.id,
        "project.create",
        "project",
        str(project.id),
        project.id,
        {"name": normalized_name},
    )
    db.commit()
    return {"id": project.id, "name": project.name}


@router.put("/projects/{project_id}")
def admin_update_project(
    project_id: int,
    payload: ProjectUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    _ensure_project_scope(admin_membership, project_id)
    project = db.scalar(select(Project).where(Project.id == project_id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    if payload.name is not None:
        normalized_name = _normalized_project_name(payload.name)
        if _project_name_exists(db, normalized_name, exclude_project_id=project_id):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Project name already exists")
        project.name = normalized_name
    if payload.description is not None:
        project.description = payload.description
    if payload.default_map_center is not None:
        project.default_center_lng = payload.default_map_center[0]
        project.default_center_lat = payload.default_map_center[1]
    if payload.default_zoom is not None:
        project.default_zoom = payload.default_zoom

    _audit(
        db,
        request,
        current_user.id,
        "project.update",
        "project",
        str(project.id),
        project.id,
        payload.model_dump(exclude_none=True),
    )
    db.commit()
    return {"ok": True}


@router.delete("/projects/{project_id}")
def admin_delete_project(
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    if not _is_super_admin(admin_membership):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SuperAdmin can delete projects")

    project = db.scalar(select(Project).where(Project.id == project_id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    _audit(
        db,
        request,
        current_user.id,
        "project.delete",
        "project",
        str(project.id),
        project.id,
        {"name": project.name},
    )
    db.delete(project)
    db.commit()
    return {"ok": True}


@router.put("/projects/{project_id}/form-fields")
def admin_replace_project_form_configuration(
    project_id: int,
    payload: list[FormFieldDefinitionPayload],
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    _ensure_project_scope(admin_membership, project_id)
    project = db.scalar(select(Project).where(Project.id == project_id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    rows = db.scalars(select(FormFieldDefinition).where(FormFieldDefinition.project_id == project_id)).all()
    for row in rows:
        db.delete(row)

    for item in payload:
        db.add(
            FormFieldDefinition(
                project_id=project_id,
                field_key=item.field_key,
                label=item.label,
                field_type=item.field_type,
                required=item.required,
                order_index=item.order_index,
                config=item.config,
            )
        )

    _audit(
        db,
        request,
        current_user.id,
        "project.form.replace",
        "project",
        str(project_id),
        project_id,
        {"fields_count": len(payload)},
    )
    db.commit()
    return {"ok": True}


@router.get("/layers")
def admin_list_layers(
    db: Session = Depends(get_db),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> list[dict]:
    if _is_super_admin(admin_membership):
        rows = db.scalars(select(Layer).order_by(Layer.id.asc())).all()
    else:
        rows = db.scalars(
            select(Layer)
            .join(ProjectLayer, ProjectLayer.layer_id == Layer.id)
            .where(ProjectLayer.project_id == admin_membership.project_id)
            .order_by(Layer.id.asc())
        ).all()

    return [
        {
            "id": row.id,
            "name": row.name,
            "geoserver_workspace": row.geoserver_workspace,
            "geoserver_layer_name": row.geoserver_layer_name,
            "style_name": row.style_name,
            "type": row.type.value,
            "default_visible": row.default_visible,
            "z_index": row.z_index,
        }
        for row in rows
    ]


@router.post("/layers", status_code=status.HTTP_201_CREATED)
def admin_create_layer(
    payload: LayerCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    if not _is_super_admin(admin_membership):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SuperAdmin can create layers")

    layer = Layer(
        name=payload.name,
        geoserver_workspace=payload.geoserver_workspace,
        geoserver_layer_name=payload.geoserver_layer_name,
        style_name=payload.style_name,
        type=LayerType(payload.type),
        default_visible=payload.default_visible,
        z_index=payload.z_index,
    )
    db.add(layer)
    db.flush()

    _audit(
        db,
        request,
        current_user.id,
        "layer.create",
        "layer",
        str(layer.id),
        None,
        payload.model_dump(),
    )
    db.commit()
    return {"id": layer.id}


@router.put("/layers/{layer_id}")
def admin_update_layer(
    layer_id: int,
    payload: LayerUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    if not _is_super_admin(admin_membership):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SuperAdmin can update layers")

    layer = db.scalar(select(Layer).where(Layer.id == layer_id))
    if not layer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")

    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        if key == "type":
            value = LayerType(value)
        setattr(layer, key, value)

    _audit(db, request, current_user.id, "layer.update", "layer", str(layer.id), None, data)
    db.commit()
    return {"ok": True}


@router.delete("/layers/{layer_id}")
def admin_delete_layer(
    layer_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    if not _is_super_admin(admin_membership):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only SuperAdmin can delete layers")

    layer = db.scalar(select(Layer).where(Layer.id == layer_id))
    if not layer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")

    _audit(db, request, current_user.id, "layer.delete", "layer", str(layer.id), None, {"name": layer.name})
    db.delete(layer)
    db.commit()
    return {"ok": True}


@router.post("/projects/{project_id}/layers")
def admin_attach_layer_to_project(
    project_id: int,
    payload: ProjectLayerAttach,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    _ensure_project_scope(admin_membership, project_id)

    project = db.scalar(select(Project).where(Project.id == project_id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    layer = db.scalar(select(Layer).where(Layer.id == payload.layer_id))
    if not layer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer not found")

    row = db.scalar(
        select(ProjectLayer).where(ProjectLayer.project_id == project_id, ProjectLayer.layer_id == payload.layer_id)
    )
    if row:
        row.available_override = payload.available_override
        row.visible_override = payload.visible_override
        row.z_index_override = payload.z_index_override
    else:
        row = ProjectLayer(
            project_id=project_id,
            layer_id=payload.layer_id,
            available_override=payload.available_override,
            visible_override=payload.visible_override,
            z_index_override=payload.z_index_override,
        )
        db.add(row)

    _audit(
        db,
        request,
        current_user.id,
        "project.layer.attach",
        "project_layer",
        f"{project_id}:{payload.layer_id}",
        project_id,
        payload.model_dump(),
    )
    db.commit()
    return {"ok": True}


@router.delete("/projects/{project_id}/layers/{layer_id}")
def admin_detach_layer_from_project(
    project_id: int,
    layer_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    _ensure_project_scope(admin_membership, project_id)

    row = db.scalar(
        select(ProjectLayer).where(ProjectLayer.project_id == project_id, ProjectLayer.layer_id == layer_id)
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Layer is not attached to project")

    _audit(
        db,
        request,
        current_user.id,
        "project.layer.detach",
        "project_layer",
        f"{project_id}:{layer_id}",
        project_id,
        {},
    )
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/users")
def admin_list_users(
    db: Session = Depends(get_db),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> list[dict]:
    if _is_super_admin(admin_membership):
        users = db.scalars(select(User).order_by(User.id.asc())).all()
    else:
        users = db.scalars(
            select(User)
            .join(UserProject, UserProject.user_id == User.id)
            .where(UserProject.project_id == admin_membership.project_id)
            .order_by(User.id.asc())
        ).all()

    out = []
    for user in users:
        memberships = db.scalars(
            select(UserProject).where(UserProject.user_id == user.id).order_by(UserProject.project_id.asc())
        ).all()
        if not _is_super_admin(admin_membership):
            memberships = [m for m in memberships if m.project_id == admin_membership.project_id]

        out.append(
            {
                "id": user.id,
                "email": user.email,
                "is_active": user.is_active,
                "projects": [
                    {
                        "project_id": membership.project_id,
                        "role": membership.role.value,
                    }
                    for membership in memberships
                ],
            }
        )

    return out


@router.post("/users", status_code=status.HTTP_201_CREATED)
def admin_create_user(
    payload: UserCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    exists = db.scalar(select(User).where(User.email == payload.email))
    if exists:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="User email already exists")

    user = User(
        email=payload.email,
        hashed_password=get_password_hash(payload.password),
        is_active=payload.is_active,
    )
    db.add(user)
    db.flush()

    if not _is_super_admin(admin_membership):
        db.add(
            UserProject(
                user_id=user.id,
                project_id=admin_membership.project_id,
                role=ProjectRole.VIEWER,
            )
        )

    _audit(db, request, current_user.id, "user.create", "user", str(user.id), None, {"email": payload.email})
    db.commit()
    return {"id": user.id}


@router.put("/users/{user_id}")
def admin_update_user(
    user_id: int,
    payload: UserUpdate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    _ensure_project_admin_can_manage_user(db, admin_membership, user_id)

    data = payload.model_dump(exclude_none=True)
    for key, value in data.items():
        if key == "password":
            user.hashed_password = get_password_hash(value)
            continue
        setattr(user, key, value)

    _audit(db, request, current_user.id, "user.update", "user", str(user.id), None, data)
    db.commit()
    return {"ok": True}


@router.delete("/users/{user_id}")
def admin_delete_user(
    user_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    _ensure_project_admin_can_manage_user(db, admin_membership, user_id)

    _audit(db, request, current_user.id, "user.delete", "user", str(user.id), None, {"email": user.email})
    db.delete(user)
    db.commit()
    return {"ok": True}


@router.post("/users/{user_id}/projects")
def admin_assign_user_to_project(
    user_id: int,
    payload: UserProjectAssign,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    user = db.scalar(select(User).where(User.id == user_id))
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

    project = db.scalar(select(Project).where(Project.id == payload.project_id))
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    _ensure_project_scope(admin_membership, payload.project_id)

    row = db.scalar(
        select(UserProject).where(UserProject.user_id == user_id, UserProject.project_id == payload.project_id)
    )
    if row:
        row.role = payload.role
    else:
        db.add(UserProject(user_id=user_id, project_id=payload.project_id, role=payload.role))

    _audit(
        db,
        request,
        current_user.id,
        "user.project.assign",
        "user_project",
        f"{user_id}:{payload.project_id}",
        payload.project_id,
        {"role": payload.role.value},
    )
    db.commit()
    return {"ok": True}


@router.delete("/users/{user_id}/projects/{project_id}")
def admin_unassign_user_from_project(
    user_id: int,
    project_id: int,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> dict:
    _ensure_project_scope(admin_membership, project_id)
    row = db.scalar(
        select(UserProject).where(UserProject.user_id == user_id, UserProject.project_id == project_id)
    )
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User is not assigned to this project")

    _audit(
        db,
        request,
        current_user.id,
        "user.project.unassign",
        "user_project",
        f"{user_id}:{project_id}",
        project_id,
        {},
    )
    db.delete(row)
    db.commit()
    return {"ok": True}


@router.get("/audit")
def admin_list_audit_logs(
    db: Session = Depends(get_db),
    admin_membership: UserProject = Depends(get_admin_membership),
) -> list[dict]:
    rows = db.scalars(select(AdminAuditLog).order_by(AdminAuditLog.id.desc()).limit(200)).all()
    if not _is_super_admin(admin_membership):
        rows = [row for row in rows if row.project_id in (None, admin_membership.project_id)]

    return [
        {
            "id": row.id,
            "actor_user_id": row.actor_user_id,
            "action": row.action,
            "target_type": row.target_type,
            "target_id": row.target_id,
            "project_id": row.project_id,
            "ip_address": row.ip_address,
            "user_agent": row.user_agent,
            "details": row.details,
            "created_at": row.created_at,
        }
        for row in rows
    ]
