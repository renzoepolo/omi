from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import get_project_membership
from app.core.database import get_db
from app.models import (
    CatalogConservationState,
    CatalogCurrency,
    CatalogDestination,
    CatalogLegalStatus,
    CatalogPropertyType,
    CatalogValueOrigin,
    Observation,
    ObservationBuilding,
    ObservationLocation,
    ObservationRural,
    ObservationStatus,
    ObservationStatusHistory,
    UserProject,
)
from app.schemas.observation import ObservationCreate, ObservationRead, ObservationUpdate

router = APIRouter(prefix="/projects/{project_id}/observations", tags=["observations"])


def _require_project_scope(project_id: int, membership: UserProject) -> None:
    if project_id != membership.project_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Project path param does not match active project scope",
        )


def _catalog_id_by_code(
    db: Session,
    model,
    code: str | None,
    *,
    required: bool = False,
) -> int | None:
    if not code:
        if required:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Missing required catalog code for {model.__tablename__}",
            )
        return None
    item = db.scalar(select(model).where(model.code == code, model.is_active.is_(True)))
    if not item:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid catalog code '{code}' for {model.__tablename__}",
        )
    return item.id


def _catalog_code_by_id(db: Session, model, item_id: int | None) -> str | None:
    if not item_id:
        return None
    item = db.scalar(select(model).where(model.id == item_id))
    return item.code if item else None


def _upsert_location(
    db: Session,
    observation: Observation,
    payload_location,
) -> None:
    if payload_location is None:
        observation.location = None
        return
    location = observation.location or ObservationLocation(observation_id=observation.id)
    location.padron = payload_location.padron
    location.neighborhood_type_code = payload_location.neighborhood_type_code
    location.shape_type_code = payload_location.shape_type_code
    location.block_position_code = payload_location.block_position_code
    location.affectation_code = payload_location.affectation_code
    location.legal_status_id = _catalog_id_by_code(
        db,
        CatalogLegalStatus,
        payload_location.legal_status_code,
        required=False,
    )
    observation.location = location


def _upsert_building(
    db: Session,
    observation: Observation,
    payload_building,
) -> None:
    if payload_building is None:
        observation.building = None
        return
    building = observation.building or ObservationBuilding(observation_id=observation.id)
    building.built_surface_total = payload_building.built_surface_total
    building.warehouse_surface = payload_building.warehouse_surface
    building.front_meters = payload_building.front_meters
    building.conservation_state_id = _catalog_id_by_code(
        db,
        CatalogConservationState,
        payload_building.conservation_state_code,
        required=False,
    )
    building.destination_id = _catalog_id_by_code(
        db,
        CatalogDestination,
        payload_building.destination_code,
        required=False,
    )
    building.construction_category_code = payload_building.construction_category_code
    building.bedrooms_count = payload_building.bedrooms_count
    building.bathrooms_count = payload_building.bathrooms_count
    building.garage_count = payload_building.garage_count
    building.floors_count = payload_building.floors_count
    building.has_pool = payload_building.has_pool
    building.antiquity_year = payload_building.antiquity_year
    observation.building = building


def _upsert_rural(
    observation: Observation,
    payload_rural,
) -> None:
    if payload_rural is None:
        observation.rural = None
        return
    rural = observation.rural or ObservationRural(observation_id=observation.id)
    rural.main_use_code = payload_rural.main_use_code
    rural.sugarcane_surface = payload_rural.sugarcane_surface
    rural.citrus_surface = payload_rural.citrus_surface
    rural.grains_surface = payload_rural.grains_surface
    rural.forest_surface = payload_rural.forest_surface
    rural.other_crops_surface = payload_rural.other_crops_surface
    rural.has_irrigation = payload_rural.has_irrigation
    rural.irrigation_type_code = payload_rural.irrigation_type_code
    rural.irrigated_surface = payload_rural.irrigated_surface
    rural.irrigation_concession_type_code = payload_rural.irrigation_concession_type_code
    rural.has_extraordinary_improvements = payload_rural.has_extraordinary_improvements
    rural.has_rural_improvements = payload_rural.has_rural_improvements
    observation.rural = rural


def _serialize_observation(db: Session, observation: Observation) -> ObservationRead:
    property_type_code = _catalog_code_by_id(db, CatalogPropertyType, observation.property_type_id)
    currency_code = _catalog_code_by_id(db, CatalogCurrency, observation.currency_id)
    value_origin_code = _catalog_code_by_id(db, CatalogValueOrigin, observation.value_origin_id)

    location = None
    if observation.location:
        location = {
            "padron": observation.location.padron,
            "neighborhood_type_code": observation.location.neighborhood_type_code,
            "shape_type_code": observation.location.shape_type_code,
            "block_position_code": observation.location.block_position_code,
            "legal_status_code": _catalog_code_by_id(db, CatalogLegalStatus, observation.location.legal_status_id),
            "affectation_code": observation.location.affectation_code,
        }

    building = None
    if observation.building:
        building = {
            "built_surface_total": observation.building.built_surface_total,
            "warehouse_surface": observation.building.warehouse_surface,
            "front_meters": observation.building.front_meters,
            "conservation_state_code": _catalog_code_by_id(
                db, CatalogConservationState, observation.building.conservation_state_id
            ),
            "destination_code": _catalog_code_by_id(db, CatalogDestination, observation.building.destination_id),
            "construction_category_code": observation.building.construction_category_code,
            "bedrooms_count": observation.building.bedrooms_count,
            "bathrooms_count": observation.building.bathrooms_count,
            "garage_count": observation.building.garage_count,
            "floors_count": observation.building.floors_count,
            "has_pool": observation.building.has_pool,
            "antiquity_year": observation.building.antiquity_year,
        }

    rural = None
    if observation.rural:
        rural = {
            "main_use_code": observation.rural.main_use_code,
            "sugarcane_surface": observation.rural.sugarcane_surface,
            "citrus_surface": observation.rural.citrus_surface,
            "grains_surface": observation.rural.grains_surface,
            "forest_surface": observation.rural.forest_surface,
            "other_crops_surface": observation.rural.other_crops_surface,
            "has_irrigation": observation.rural.has_irrigation,
            "irrigation_type_code": observation.rural.irrigation_type_code,
            "irrigated_surface": observation.rural.irrigated_surface,
            "irrigation_concession_type_code": observation.rural.irrigation_concession_type_code,
            "has_extraordinary_improvements": observation.rural.has_extraordinary_improvements,
            "has_rural_improvements": observation.rural.has_rural_improvements,
        }

    return ObservationRead(
        id=observation.id,
        project_id=observation.project_id,
        property_type=property_type_code,
        status=observation.status.value,
        price=observation.market_value_total,
        currency=currency_code,
        valuation_date=observation.valuation_date,
        unit_land_value=observation.unit_land_value,
        surface_total=observation.surface_total,
        surface_unit=observation.surface_unit,
        value_origin_code=value_origin_code,
        external_uuid=observation.external_uuid,
        legacy_fid=observation.legacy_fid,
        extras=observation.extras or {},
        location=location,
        building=building,
        rural=rural,
        created_at=observation.created_at,
        updated_at=observation.updated_at,
    )


@router.get("", response_model=list[ObservationRead])
def list_observations(
    project_id: int,
    membership: UserProject = Depends(get_project_membership),
    db: Session = Depends(get_db),
) -> list[ObservationRead]:
    _require_project_scope(project_id, membership)
    items = db.scalars(
        select(Observation)
        .where(Observation.project_id == project_id, Observation.deleted_at.is_(None))
        .order_by(Observation.created_at.desc())
    ).all()
    return [_serialize_observation(db, item) for item in items]


@router.post("", response_model=ObservationRead, status_code=status.HTTP_201_CREATED)
def create_observation(
    project_id: int,
    payload: ObservationCreate,
    membership: UserProject = Depends(get_project_membership),
    db: Session = Depends(get_db),
) -> ObservationRead:
    _require_project_scope(project_id, membership)
    if payload.project_id != project_id:
        raise HTTPException(status_code=400, detail="project_id body and path must match")

    observation = Observation(
        project_id=project_id,
        external_uuid=payload.external_uuid,
        legacy_fid=payload.legacy_fid,
        property_type_id=_catalog_id_by_code(db, CatalogPropertyType, payload.property_type.value, required=True),
        value_origin_id=_catalog_id_by_code(db, CatalogValueOrigin, payload.value_origin_code, required=False),
        currency_id=_catalog_id_by_code(
            db, CatalogCurrency, payload.currency.value if payload.currency else None, required=False
        ),
        market_value_total=payload.price,
        unit_land_value=payload.unit_land_value,
        valuation_date=payload.valuation_date,
        surface_total=payload.surface_total,
        surface_unit=payload.surface_unit,
        status=ObservationStatus(payload.status.value),
        is_outlier=payload.status.value == ObservationStatus.OUTLIER.value,
        created_by=membership.user_id,
        updated_by=membership.user_id,
        extras=payload.extras,
    )
    db.add(observation)
    db.flush()

    _upsert_location(db, observation, payload.location)
    _upsert_building(db, observation, payload.building)
    _upsert_rural(observation, payload.rural)

    db.add(
        ObservationStatusHistory(
            observation_id=observation.id,
            from_status=None,
            to_status=observation.status,
            changed_by=membership.user_id,
            reason="create",
        )
    )
    db.commit()
    db.refresh(observation)
    return _serialize_observation(db, observation)


@router.patch("/{observation_id}", response_model=ObservationRead)
def update_observation(
    project_id: int,
    observation_id: UUID,
    payload: ObservationUpdate,
    membership: UserProject = Depends(get_project_membership),
    db: Session = Depends(get_db),
) -> ObservationRead:
    _require_project_scope(project_id, membership)
    observation = db.scalar(
        select(Observation).where(
            Observation.id == observation_id,
            Observation.project_id == project_id,
            Observation.deleted_at.is_(None),
        )
    )
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")

    before_status = observation.status
    data = payload.model_dump(exclude_unset=True)

    if "property_type" in data:
        observation.property_type_id = _catalog_id_by_code(
            db, CatalogPropertyType, payload.property_type.value, required=True
        )
    if "value_origin_code" in data:
        observation.value_origin_id = _catalog_id_by_code(
            db, CatalogValueOrigin, payload.value_origin_code, required=False
        )
    if "currency" in data:
        observation.currency_id = _catalog_id_by_code(
            db, CatalogCurrency, payload.currency.value if payload.currency else None, required=False
        )
    if "price" in data:
        observation.market_value_total = payload.price
    if "unit_land_value" in data:
        observation.unit_land_value = payload.unit_land_value
    if "valuation_date" in data:
        observation.valuation_date = payload.valuation_date
    if "surface_total" in data:
        observation.surface_total = payload.surface_total
    if "surface_unit" in data:
        observation.surface_unit = payload.surface_unit
    if "status" in data:
        observation.status = ObservationStatus(payload.status.value)
        observation.is_outlier = observation.status == ObservationStatus.OUTLIER
        if observation.status == ObservationStatus.ELIMINADO:
            observation.deleted_at = datetime.utcnow()
    if "extras" in data and payload.extras is not None:
        observation.extras = payload.extras

    if "location" in data:
        _upsert_location(db, observation, payload.location)
    if "building" in data:
        _upsert_building(db, observation, payload.building)
    if "rural" in data:
        _upsert_rural(observation, payload.rural)

    observation.updated_by = membership.user_id

    if before_status != observation.status:
        db.add(
            ObservationStatusHistory(
                observation_id=observation.id,
                from_status=before_status,
                to_status=observation.status,
                changed_by=membership.user_id,
                reason="update",
            )
        )

    db.commit()
    db.refresh(observation)
    return _serialize_observation(db, observation)


@router.delete("/{observation_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_observation(
    project_id: int,
    observation_id: UUID,
    membership: UserProject = Depends(get_project_membership),
    db: Session = Depends(get_db),
) -> None:
    _require_project_scope(project_id, membership)
    observation = db.scalar(
        select(Observation).where(
            Observation.id == observation_id,
            Observation.project_id == project_id,
            Observation.deleted_at.is_(None),
        )
    )
    if not observation:
        raise HTTPException(status_code=404, detail="Observation not found")

    before_status = observation.status
    observation.status = ObservationStatus.ELIMINADO
    observation.is_outlier = False
    observation.deleted_at = datetime.utcnow()
    observation.updated_by = membership.user_id

    db.add(
        ObservationStatusHistory(
            observation_id=observation.id,
            from_status=before_status,
            to_status=ObservationStatus.ELIMINADO,
            changed_by=membership.user_id,
            reason="delete",
        )
    )
    db.commit()
