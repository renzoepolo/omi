# Observatorio de Valores Inmobiliarios (OVI) — Diseño técnico inicial

## 1) Análisis de la estructura del diccionario de datos

Se analizó la tabla `OVI.dbf` con 54 campos funcionales (más metadatos del diccionario). El modelo original mezcla en una sola tabla:

- Identificación y trazabilidad (`FID`, `UUID`, usuarios/fechas de alta y modificación).
- Variables económicas (`VALOR_TOTAL`, `VUT`, `MONEDA`, `FECHA_VALOR`, `ORIGEN_VALOR`).
- Variables físicas del inmueble (`SUPERFICIE`, `FRENTE`, `SUP_EDIT_TOTAL`, `N_DORMITORIO`, `N_BANO`, etc.).
- Variables contextuales/jurídicas (`SIT_JURIDICA`, `AFECTACION`, `CALIDAD_UBIC`, `PADRON`).
- Variables rurales específicas (`USO_PPAL`, `SUP_CANA`, `RIEGO`, `TIPO_RIEGO`, etc.).
- Evidencias y texto libre (`FOTO_FACHADA`, `FOTO_CARTEL`, `CAPTURA`, `OBS`, `LINK`, `TELEFONO`).
- Catálogos codificados “0/1/2/…” embebidos como texto en el diccionario.

### Hallazgos de modelado

1. **Sobrecarga de una tabla única**: conviven atributos de urbano y rural, ocasionando nulos masivos y baja calidad de datos.
2. **Catálogos codificados**: requieren normalización para evitar hardcode, permitir cambios de negocio y facilitar analítica.
3. **Metadatos operativos y de negocio mezclados**: conviene separar estado del registro, historial de cambios y evidencias.
4. **Campos de alta variabilidad por fuente**: algunos atributos son candidatos naturales para `JSONB` controlado por esquema/versionado.
5. **`ESTADO_CARGA` se excluye del diseño** por requerimiento, reemplazándolo por un estado de ciclo de vida robusto.

> Nota: por requerimiento, se ignoran `longitud`, `precisión` y `estado_carga` como componentes de diseño final.

---

## 2) Propuesta de modelo SQLAlchemy normalizado (sin código)

### 2.1 Entidades principales

## `projects`
Representa el tenant lógico.

- `id` (PK)
- `name`
- `slug` (único)
- `is_active`
- `created_at`, `updated_at`

## `observations`
Entidad raíz del punto/observación.

- `id` (PK, UUID)
- `project_id` (FK → `projects.id`, obligatorio)
- `external_uuid` (UUID origen Kobo / scraping)
- `legacy_fid` (opcional, trazabilidad migración)
- `property_type_id` (FK catálogo)
- `value_origin_id` (FK catálogo)
- `currency_id` (FK catálogo)
- `market_value_total` (numeric)
- `unit_land_value` (numeric)
- `valuation_date` (date)
- `surface_total` (numeric)
- `surface_unit_id` (FK catálogo)
- `status` (enum controlado por workflow)
- `is_outlier` (bool derivado/operativo)
- `deleted_at` (soft delete)
- `created_by`, `updated_by`
- `created_at`, `updated_at`
- `extras` (JSONB acotado para extensibilidad)

Índices sugeridos:
- `(project_id, status)`
- `(project_id, valuation_date)`
- `(project_id, market_value_total)`
- `(project_id, deleted_at)` parcial para activos
- GIN sobre `extras`

## `observation_location`
Ubicación y referencia catastral (1:1 con observación).

- `observation_id` (PK/FK)
- `padron`
- `location_quality_id` (FK catálogo)
- `block_position_id` (FK catálogo)
- `neighborhood_type_id` (FK catálogo)
- `shape_type_id` (FK catálogo)
- `legal_status_id` (FK catálogo)
- `affectation_type_id` (FK catálogo)

> Se reserva extensión futura para geolocalización precisa cuando exista fuente consistente.

## `observation_building`
Atributos constructivos/urbanos (1:1 opcional).

- `observation_id` (PK/FK)
- `built_surface_total`
- `warehouse_surface`
- `front_meters`
- `conservation_state_id` (FK catálogo)
- `destination_id` (FK catálogo)
- `construction_category_id` (FK catálogo)
- `bedrooms_count`
- `bathrooms_count`
- `garage_count`
- `floors_count`
- `has_pool` (bool)
- `antiquity_year`

## `observation_rural`
Atributos rurales (1:1 opcional).

- `observation_id` (PK/FK)
- `main_use_id` (FK catálogo)
- `sugarcane_surface`
- `citrus_surface`
- `grains_surface`
- `forest_surface`
- `other_crops_surface`
- `has_irrigation` (bool)
- `irrigation_type_id` (FK catálogo)
- `irrigated_surface`
- `irrigation_concession_type_id` (FK catálogo)
- `has_extraordinary_improvements` (bool)
- `has_rural_improvements` (bool)

## `observation_sources`
Datos de fuente/contacto (1:N).

- `id` (PK)
- `observation_id` (FK)
- `source_type_id` (FK catálogo: campo/web/agente/scraping)
- `url`
- `phone`
- `notes`
- `captured_at`

Permite múltiples fuentes por observación (muy útil para consolidación).

## `observation_media`
Evidencia multimedia (1:N).

- `id` (PK)
- `observation_id` (FK)
- `media_type` (enum: fachada, cartel, captura, audio, otro)
- `storage_url`
- `checksum`
- `metadata` (JSONB)
- `created_at`

## `observation_notes`
Notas libres y observaciones no estructuradas (1:N).

- `id` (PK)
- `observation_id` (FK)
- `note_type` (enum: interna, validación, relevamiento)
- `content`
- `created_by`
- `created_at`

## `observation_status_history`
Historial de estados (1:N) para auditoría y trazabilidad.

- `id` (PK)
- `observation_id` (FK)
- `from_status`
- `to_status`
- `changed_by`
- `reason`
- `changed_at`

## `catalog_*` (dimensiones)
Tablas maestras para catálogos (valor + etiqueta + vigencia), por ejemplo:

- `catalog_property_type`
- `catalog_currency`
- `catalog_value_origin`
- `catalog_legal_status`
- `catalog_neighborhood_type`
- `catalog_destination`
- `catalog_conservation_state`
- etc.

Patrón común:
- `id` (PK)
- `code` (estable)
- `label`
- `description`
- `is_active`
- `sort_order`

---

## 3) Qué va a columnas fijas vs JSONB dinámico vs tablas relacionadas

### 3.1 Columnas fijas (núcleo transaccional)
Deben ser columnas explícitas en `observations` por uso intensivo en filtros, reglas e indicadores:

- Identidad/tenant: `id`, `project_id`, `external_uuid`, `legacy_fid`
- Económico: `market_value_total`, `unit_land_value`, `currency_id`, `valuation_date`, `value_origin_id`
- Clasificación primaria: `property_type_id`
- Magnitud base: `surface_total`, `surface_unit_id`
- Operativo: `status`, `is_outlier`, `deleted_at`, `created_at`, `updated_at`, `created_by`, `updated_by`

### 3.2 JSONB dinámico (controlado)
Usar `extras` para atributos **poco frecuentes, emergentes o de integraciones** que no justifican columna inmediata:

- Metadatos de scraping no estables.
- Payload técnico de conectores externos.
- Flags temporales de calidad/corrección manual.
- Campos experimentales en pilotos por proyecto.

Regla de gobierno recomendada:
- Si un atributo aparece en >20% de registros de ≥2 proyectos y se usa en queries recurrentes, migrarlo a columna o tabla formal.

### 3.3 Tablas relacionadas
Mover a tablas relacionadas cuando haya:

1. **Cardinalidad múltiple** (fuentes, media, notas).
2. **Semántica de dominio especializada** (rural vs urbano).
3. **Necesidad de auditoría detallada** (historial de estado).
4. **Catálogos mantenibles** (evitar “0-1-2-3” hardcodeado).

---

## 4) Modelo de estados propuesto

Estados requeridos:
- `cargado`
- `posicionado`
- `revision`
- `completado`
- `outlier`
- `eliminado`

### 4.1 Definición operacional

- **cargado**: registro ingresado con datos mínimos obligatorios.
- **posicionado**: validación mínima de ubicación/referencia catastral.
- **revision**: registro bajo control de calidad (manual o reglas).
- **completado**: registro apto para análisis/publicación interna.
- **outlier**: registro detectado como valor atípico (estadística o regla experta).
- **eliminado**: baja lógica (no borrado físico).

### 4.2 Máquina de estados (transiciones)

Transiciones permitidas recomendadas:

- `cargado -> posicionado | revision | eliminado`
- `posicionado -> revision | completado | eliminado`
- `revision -> completado | outlier | eliminado`
- `outlier -> revision | completado | eliminado`
- `completado -> revision | outlier | eliminado`
- `eliminado` terminal (solo reactivación por acción administrativa explícita: `eliminado -> revision`)

### 4.3 Reglas de negocio mínimas

- No pasar a `completado` sin: valor, moneda, fecha de valor, tipo de inmueble y superficie.
- `outlier` no implica eliminación: permanece visible para analistas con bandera explícita.
- Todo cambio de estado escribe en `observation_status_history` con usuario y motivo.

---

## 5) Esquema multi-tenant por `project_id`

## Estrategia recomendada: **tabla compartida + discriminador `project_id`**

Ventajas:
- Menor complejidad operativa que “schema por tenant”.
- Consultas cross-project sencillas para benchmarking.
- Menor costo de migraciones y despliegues.

### Reglas técnicas

1. **`project_id` obligatorio** en todas las tablas de negocio (o inferible por FK directa a `observations`).
2. **Índices compuestos** iniciando por `project_id`.
3. **Restricciones de unicidad por tenant**, por ejemplo: `unique(project_id, external_uuid)`.
4. **Row Level Security (RLS)** en PostgreSQL para aislamiento fuerte por proyecto.
5. **Particionado opcional por `project_id` o por fecha** cuando el volumen lo requiera.

### Patrón de seguridad

- Contexto de aplicación define `current_project_id` por request.
- Toda query se filtra por tenant.
- RLS valida en base de datos que no haya escapes por error de código.

---

## 6) Decisiones de arquitectura (antes de escribir código)

1. **Normalización pragmática**: separar núcleo, catálogos y subdominios (urbano/rural) para evitar nulos y ambigüedades.
2. **`JSONB` con gobernanza**: habilita evolución rápida sin degradar el modelo relacional principal.
3. **Estado como workflow explícito**: reemplaza `estado_carga` legacy por máquina auditable.
4. **Multi-tenant por discriminador**: equilibrio entre aislamiento, costo operativo y escalabilidad.
5. **Auditoría first-class**: historial de estados + trazabilidad de usuario desde el inicio.
6. **Soft delete**: preserva evidencia y evita pérdida irreversible de información de mercado.
7. **Catálogos desacoplados**: evita recodificar enums ante cambios normativos/operativos.

---

## 7) Fase sugerida para implementación posterior

1. Crear tablas base: `projects`, `observations`, catálogos clave, `status_history`.
2. Incorporar `observation_location`, `observation_building`, `observation_rural`.
3. Agregar `sources`, `media`, `notes`.
4. Definir validaciones de transición de estado + RLS por `project_id`.
5. Diseñar migrador desde estructura legacy.

