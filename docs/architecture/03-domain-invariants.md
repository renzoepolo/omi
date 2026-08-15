# Invariantes del dominio

Reglas que el código asume en todas partes. Romper cualquiera de ellas produce
fallas silenciosas o filtraciones de datos entre proyectos, así que conviene
leerlas antes de tocar `app/` o `src/lib/api.js`.

## 1. Multi-tenancy: el proyecto es el tenant

- Todo request a una ruta no exenta lleva el header **`X-Project-Id`** con un
  valor numérico. Sin él la respuesta es **400** (`app/main.py`).
- El backend nunca confía en el `project_id` del body ni del path: el scope
  real sale del header y se valida contra `user_projects`
  (`get_project_membership` en `app/api/deps.py`).
- En `app/api/routes/observations.py`, `_require_project_scope` exige además
  que el `project_id` del path coincida con el scope activo, y
  `create_observation` verifica que el `project_id` del body también coincida.
- Toda consulta de observaciones filtra por `project_id` **y** por
  `deleted_at IS NULL`.

Cuando agregues una tabla con datos de negocio, necesita `project_id` con FK a
`projects` y borrado en cascada, y toda query sobre ella debe filtrar por el
proyecto activo.

## 2. Roles

Los cuatro roles viven en `ProjectRole` (`app/models/user_project.py`):
`SuperAdmin`, `ProjectAdmin`, `Editor`, `Viewer`. Se asignan **por proyecto**,
no globalmente: un mismo usuario puede ser `SuperAdmin` en un proyecto y
`Editor` en otro.

- `get_admin_membership` restringe `/admin/*` a `SuperAdmin` y `ProjectAdmin`.
- Dentro de `/admin`, `_ensure_project_scope` deja que `SuperAdmin` opere sobre
  cualquier proyecto, mientras que `ProjectAdmin` queda limitado al suyo.

> **Hueco conocido.** Los endpoints de observaciones (`POST`, `PATCH`,
> `DELETE`) sólo exigen pertenencia al proyecto vía `get_project_membership`;
> no comprueban el rol. Un usuario con rol `Viewer` puede escribir
> observaciones llamando la API directamente. El frontend oculta las
> herramientas de edición, pero eso es una restricción de UI, no de seguridad.
> Cerrarlo requiere una dependencia tipo `get_editor_membership` que rechace
> `Viewer`.

## 3. Row Level Security: definido pero no conectado

`db/migrations/20260218_enable_multi_tenant_rls.sql` activa RLS sobre toda
tabla que tenga una columna `project_id`, con una política que compara contra
`current_setting('app.current_project_id')`. Se aplica con
`scripts/apply_rls.sh` y sólo si `ENABLE_RLS=true`.

**El backend nunca setea esa variable de sesión.** No hay ningún `set_config`
ni `SET LOCAL app.current_project_id` en `app/`. Si se activara RLS tal como
está hoy, la política no encontraría valor y las consultas devolverían cero
filas.

El aislamiento efectivo hoy es el de la capa de aplicación descrito en el punto
1. Activar RLS es un cambio pendiente que exige, además de correr el script,
fijar `app.current_project_id` en cada sesión de SQLAlchemy a partir del scope
del request.

## 4. `shared/ovi_enums.json` es la única fuente de verdad de los códigos OVI

El mismo archivo lo consumen los dos lados:

- El backend, vía `app/core/ovi_enums.py` (cacheado con `lru_cache`), para
  validar en `OviUrbanoBaldioPayload`.
- El frontend, importándolo directamente en
  `src/components/RightPanel.jsx`, para poblar los `select` y validar el
  formulario.

Agregar, quitar o renumerar un código se hace **sólo en ese archivo**. Nunca
hardcodees un código OVI en Python o en JSX: se desincronizan los dos lados sin
que ningún test lo note.

`Dockerfile.backend` y `Dockerfile.frontend` copian `shared/` explícitamente;
si movés el archivo, hay que actualizar ambos.

## 5. Reglas de negocio del bloque OVI urbano baldío

Validadas en `OviUrbanoBaldioPayload.validate_business_rules`
(`app/schemas/observation.py`) y replicadas en `isOviUrbanoBaldioValid`
(`src/components/RightPanel.jsx`). Si tocás una, tocá las dos.

- Todo campo enumerado debe tener un código presente en `shared/ovi_enums.json`.
- `TIPO_INMUEBLE` debe ser `0` (urbano baldío) y `UNI_SUP` debe ser `0`
  (metros).
- Según `PROCEDENCIA`:
  - `0` (relevamiento de campo): `FOTO_FACHADA` y `FOTO_CARTEL` obligatorias,
    `LINK` debe ser nulo.
  - `1` (sitio web): `LINK` obligatorio, ambas fotos deben ser nulas.
  - cualquier otro valor: fotos y `LINK` nulos.

## 6. Coherencia del payload de observación

En `ObservationBase` (`app/schemas/observation.py`):

- `price` y `currency` van siempre juntos: uno sin el otro es error de
  validación.
- `property_type` determina qué bloques de detalle se aceptan:
  - `rural` → admite `rural`, prohíbe `building`.
  - `urbano_baldio` / `urbano_edificado` → admiten `building`, prohíben
    `rural`.
  - `urbano_baldio` → **exige** `ovi_urbano_baldio`; cualquier otro tipo lo
    prohíbe.
- Todos los payloads usan `extra="forbid"`: un campo desconocido es un 422, no
  un campo ignorado.

## 7. Catálogos: la API habla por `code`, la base guarda `id`

Las tablas `catalog_*` tienen `id` numérico y `code` textual. Los payloads y
las respuestas de la API usan siempre `code`; la traducción ocurre en los
helpers `_catalog_id_by_code` y `_catalog_code_by_id`.

Un código inexistente o con `is_active = false` produce **400**, no 404. Al
agregar un catálogo nuevo hay que sembrarlo en la migración correspondiente:
si la fila no existe, toda alta que lo referencie falla.

## 8. Estados y borrado lógico

`ObservationStatus` define `cargado`, `posicionado`, `revision`, `completado`,
`outlier` y `eliminado`.

- El borrado es lógico: `DELETE` marca `status = eliminado` y setea
  `deleted_at`. La fila nunca se borra.
- `is_outlier` se mantiene en sincronía con `status == outlier`.
- **Todo cambio de estado escribe una fila en `observation_status_history`**
  con el usuario y un motivo (`create`, `update`, `delete`).

> **Hueco conocido.** `docs/ovi_diseno_tecnico.md` §4.2 define una máquina de
> estados con transiciones permitidas, y §4.3 exige valor, moneda, fecha,
> tipo y superficie para pasar a `completado`. Nada de eso está implementado:
> `update_observation` acepta cualquier estado desde cualquier otro. Hoy la
> historia se registra, pero no se restringe.

## 9. `extras` es un JSONB con contrato

`observations.extras` guarda datos que no tienen columna propia. Dos reglas:

- `_sanitize_extras` elimina siempre las claves `name` y `description` antes de
  persistir.
- La clave **`coordinates`** contiene el par `[lon, lat]` del punto y es lo que
  usa el visor para dibujar. No es un campo libre: perderlo deja la observación
  sin ubicación en el mapa (el frontend cae a un default de Lima,
  `[-77.0428, -12.0464]`).

## 10. El modo demo del frontend

Si `VITE_API_URL` está vacío, `src/lib/api.js` no llama a ningún backend:
autentica contra `admin@omi.local / admin123`, devuelve dos proyectos ficticios
y guarda los puntos en `localStorage`. El panel de administración lanza un
error explícito en ese modo.

Es útil para desarrollo de UI, pero significa que **una pantalla que "funciona"
en local puede no estar tocando la API en absoluto**. Ante un comportamiento
raro del frontend, lo primero es confirmar el valor de `VITE_API_URL`.
