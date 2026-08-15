<!-- GENERADO POR scripts/build_repo_graph.py — NO EDITAR A MANO -->

# Modelo de datos

Entidades derivadas de los modelos SQLAlchemy en `app/models/`.
Las relaciones son claves foráneas declaradas en el código.

```mermaid
erDiagram
  admin_audit_logs {
    col id PK
    col actor_user_id FK
    col action
    col target_type
    col target_id
    col project_id FK
    col ip_address
    col user_agent
    col details
    col created_at
  }
  catalog_conservation_state {
    col id PK
    col code
    col label
    col description
    col is_active
    col sort_order
  }
  catalog_currency {
    col id PK
    col code
    col label
    col description
    col is_active
    col sort_order
  }
  catalog_destination {
    col id PK
    col code
    col label
    col description
    col is_active
    col sort_order
  }
  catalog_legal_status {
    col id PK
    col code
    col label
    col description
    col is_active
    col sort_order
  }
  catalog_property_type {
    col id PK
    col code
    col label
    col description
    col is_active
    col sort_order
  }
  catalog_value_origin {
    col id PK
    col code
    col label
    col description
    col is_active
    col sort_order
  }
  form_field_definitions {
    col id PK
    col project_id FK
    col field_key
    col label
    col field_type
    col required
    col order_index
    col config
  }
  layers {
    col id PK
    col name
    col geoserver_workspace
    col geoserver_layer_name
    col style_name
    col type
    col default_visible
    col z_index
  }
  observation_building {
    col observation_id PK
    col built_surface_total
    col warehouse_surface
    col front_meters
    col conservation_state_id FK
    col destination_id FK
    col construction_category_code
    col bedrooms_count
    col bathrooms_count
    col garage_count
    col floors_count
    col has_pool
    col antiquity_year
  }
  observation_location {
    col observation_id PK
    col padron
    col neighborhood_type_code
    col shape_type_code
    col block_position_code
    col legal_status_id FK
    col affectation_code
  }
  observation_ovi_urbano_baldio {
    col observation_id PK
    col tipo_inmueble
    col origen_valor
    col superficie
    col uni_sup
    col moneda
    col valor_total
    col nomenclatura
    col afectacion
    col frente
    col forma
    col ubic_cuadra
    col tipo_barrio
    col sit_juridica
    col fecha_valor
    col procedencia
    col telefono
    col foto_fachada
    col foto_cartel
    col link
  }
  observation_rural {
    col observation_id PK
    col main_use_code
    col sugarcane_surface
    col citrus_surface
    col grains_surface
    col forest_surface
    col other_crops_surface
    col has_irrigation
    col irrigation_type_code
    col irrigated_surface
    col irrigation_concession_type_code
    col has_extraordinary_improvements
    col has_rural_improvements
  }
  observation_status_history {
    col id PK
    col observation_id FK
    col from_status
    col to_status
    col changed_by FK
    col reason
    col changed_at
  }
  observations {
    col id PK
    col project_id FK
    col external_uuid
    col legacy_fid
    col property_type_id FK
    col value_origin_id FK
    col currency_id FK
    col market_value_total
    col unit_land_value
    col valuation_date
    col surface_total
    col surface_unit
    col status
    col is_outlier
    col deleted_at
    col created_by FK
    col updated_by FK
    col created_at
    col updated_at
    col extras
  }
  project_layers {
    col id PK
    col project_id FK
    col layer_id FK
    col available_override
    col visible_override
    col z_index_override
  }
  projects {
    col id PK
    col name
    col description
    col default_center_lng
    col default_center_lat
    col default_zoom
  }
  user_projects {
    col id PK
    col user_id FK
    col project_id FK
    col role
  }
  users {
    col id PK
    col email
    col hashed_password
    col is_active
  }
  users ||--o{ admin_audit_logs : "actor_user_id"
  projects ||--o{ admin_audit_logs : "project_id"
  projects ||--o{ form_field_definitions : "project_id"
  observations ||--|| observation_building : "observation_id"
  catalog_conservation_state ||--o{ observation_building : "conservation_state_id"
  catalog_destination ||--o{ observation_building : "destination_id"
  observations ||--|| observation_location : "observation_id"
  catalog_legal_status ||--o{ observation_location : "legal_status_id"
  observations ||--|| observation_ovi_urbano_baldio : "observation_id"
  observations ||--|| observation_rural : "observation_id"
  observations ||--o{ observation_status_history : "observation_id"
  users ||--o{ observation_status_history : "changed_by"
  projects ||--o{ observations : "project_id"
  catalog_property_type ||--o{ observations : "property_type_id"
  catalog_value_origin ||--o{ observations : "value_origin_id"
  catalog_currency ||--o{ observations : "currency_id"
  users ||--o{ observations : "created_by"
  users ||--o{ observations : "updated_by"
  projects ||--o{ project_layers : "project_id"
  layers ||--o{ project_layers : "layer_id"
  users ||--o{ user_projects : "user_id"
  projects ||--o{ user_projects : "project_id"
```

## Tablas

| Tabla | Modelo | Archivo | Columnas |
| --- | --- | --- | --- |
| `admin_audit_logs` | `AdminAuditLog` | `app/models/admin.py` | 10 |
| `catalog_conservation_state` | `CatalogConservationState` | `app/models/catalogs.py` | 6 |
| `catalog_currency` | `CatalogCurrency` | `app/models/catalogs.py` | 6 |
| `catalog_destination` | `CatalogDestination` | `app/models/catalogs.py` | 6 |
| `catalog_legal_status` | `CatalogLegalStatus` | `app/models/catalogs.py` | 6 |
| `catalog_property_type` | `CatalogPropertyType` | `app/models/catalogs.py` | 6 |
| `catalog_value_origin` | `CatalogValueOrigin` | `app/models/catalogs.py` | 6 |
| `form_field_definitions` | `FormFieldDefinition` | `app/models/admin.py` | 8 |
| `layers` | `Layer` | `app/models/admin.py` | 8 |
| `observation_building` | `ObservationBuilding` | `app/models/observation.py` | 13 |
| `observation_location` | `ObservationLocation` | `app/models/observation.py` | 7 |
| `observation_ovi_urbano_baldio` | `ObservationOviUrbanoBaldio` | `app/models/observation.py` | 20 |
| `observation_rural` | `ObservationRural` | `app/models/observation.py` | 13 |
| `observation_status_history` | `ObservationStatusHistory` | `app/models/observation.py` | 7 |
| `observations` | `Observation` | `app/models/observation.py` | 20 |
| `project_layers` | `ProjectLayer` | `app/models/admin.py` | 6 |
| `projects` | `Project` | `app/models/project.py` | 6 |
| `user_projects` | `UserProject` | `app/models/user_project.py` | 4 |
| `users` | `User` | `app/models/user.py` | 4 |
