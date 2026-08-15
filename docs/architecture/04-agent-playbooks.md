# Playbooks

Recetas para las tareas de cambio más frecuentes. Cada una lista los archivos
que hay que tocar en orden y cómo verificar el resultado. Están pensadas para
que un agente de IA no tenga que redescubrir la topología del repositorio en
cada sesión.

## Comandos base

```bash
# Backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head              # aplica el esquema
python -m scripts.seed            # usuarios, proyectos y capas de ejemplo
uvicorn app.main:app --reload     # API en http://localhost:8000
python -m pytest -q               # 36 tests, SQLite en memoria

# Frontend
npm install
npm run dev                       # http://localhost:5173
npm test                          # vitest
npm run lint

# Documentación
python scripts/build_repo_graph.py          # regenera el grafo del repositorio
python scripts/build_repo_graph.py --check  # falla si quedó desactualizado

# Stack completo
docker compose -f docker-compose.app.yml up --build   # visor en :8500
```

Los tests del backend usan SQLite en memoria (`tests/conftest.py`), así que
corren sin PostgreSQL. La contrapartida es que **no validan nada específico de
PostgreSQL**: JSONB, RLS o tipos PostGIS pasan de largo. Un cambio que dependa
de esas features necesita verificación manual contra la base real.

## Agregar un campo al bloque OVI urbano baldío

El caso más común y el que más lugares toca. Orden sugerido:

1. **`shared/ovi_enums.json`** — sólo si el campo es enumerado. Nunca
   hardcodees los códigos en otro lado.
2. **`app/models/observation.py`** — agregá la columna en
   `ObservationOviUrbanoBaldio`.
3. **Migración Alembic** — ver el playbook siguiente.
4. **`app/schemas/observation.py`** — el campo en `OviUrbanoBaldioPayload`, con
   su validación en `validate_business_rules` si corresponde.
5. **`app/api/routes/observations.py`** — asignación en
   `_upsert_ovi_urbano_baldio` y lectura en `_serialize_observation`. Son dos
   funciones distintas; olvidar la segunda hace que el campo se guarde pero no
   se devuelva.
6. **`src/components/RightPanel.jsx`** — el control del formulario y, si hay
   regla nueva, `isOviUrbanoBaldioValid`.
7. **`src/lib/api.js`** — la conversión en `toPayload` si el campo es numérico
   (el formulario produce strings).
8. **`src/App.jsx`** — el valor inicial en `buildPoint`.
9. **`tests/test_observation_schema.py`** — un caso válido y uno inválido.

Verificación: `python -m pytest -q` y `npm test`.

## Crear una migración

```bash
alembic revision --autogenerate -m "descripcion_corta"
```

`alembic/env.py` expone `target_metadata = Base.metadata`, así que el
autogenerado compara los modelos contra la base y funciona. Toma la URL de
`settings.database_url`, ignorando la de `alembic.ini`: hace falta una
PostgreSQL viva y `DATABASE_URL` apuntando a ella.

El diff autogenerado siempre se revisa a mano. Alembic no detecta bien los
cambios de tipo de columna ni los `server_default`, y el `Enum(...,
native_enum=False)` que usan los modelos se materializa como `VARCHAR` con
`CHECK`, que suele necesitar ajuste.

Convención de nombres en `alembic/versions/`: `AAAAMMDD_NNNN_slug.py`
(por ejemplo `20260219_0007_ovi_urbano_baldio.py`), donde `NNNN` es un contador
secuencial. No hay `file_template` configurado en `alembic.ini`, así que el
archivo generado hay que **renombrarlo a mano** para respetar la convención.

Recordá que `docker/backend-entrypoint.sh` corre `alembic upgrade head` en cada
arranque del contenedor: una migración que falla deja el backend sin levantar.

## Agregar un endpoint a la API

1. Elegí el router en `app/api/routes/` según el recurso, o creá uno nuevo con
   `APIRouter(prefix=..., tags=[...])` y registralo en `app/api/router.py`.
2. Declará las dependencias de autorización según el nivel de acceso:
   - lectura o escritura dentro de un proyecto →
     `membership: UserProject = Depends(get_project_membership)`
   - operación de administración → `Depends(get_admin_membership)`
   - operación sin scope de proyecto → `Depends(get_current_user)` **y**
     agregar la ruta a `PROJECT_ID_EXEMPT_PATHS` en `app/main.py`.
3. Si la ruta lleva `{project_id}` en el path, llamá a `_require_project_scope`
   para que no difiera del scope del header.
4. Definí los schemas de entrada y salida en `app/schemas/` con
   `ConfigDict(extra="forbid")`.
5. Regenerá el grafo: `python scripts/build_repo_graph.py`.

Si el endpoint es de `/admin` y muta datos, tiene que llamar a `_audit` antes
del commit: es la única manera de que la acción quede en `admin_audit_logs`.

## Agregar una capa de GeoServer a un proyecto

Desde el panel (`/admin`, pestaña *Capas*) el flujo es: elegir workspace →
elegir capa → registrarla en `layers` → asociarla al proyecto en
`project_layers` con sus overrides.

Programáticamente son dos llamadas: `POST /admin/layers` y luego
`POST /admin/projects/{project_id}/layers`.

Los overrides de `project_layers` (`available_override`, `visible_override`,
`z_index_override`) son `NULL`-ables: `NULL` significa "usar el valor por
defecto de la capa". Esa resolución ocurre en `_serialize_project_summary`
(`app/api/routes/projects.py`), que es lo que consume `MapView.jsx`.

Sólo se renderizan las capas de tipo `WMS`; las `WFS` quedan registradas pero
`MapView.jsx` las filtra.

## Diagnosticar un error de la API

| Síntoma | Causa habitual |
| --- | --- |
| `400 Missing X-Project-Id header` | El request no mandó el header y la ruta no está en `PROJECT_ID_EXEMPT_PATHS`. |
| `400 X-Project-Id must be numeric` | Se mandó un slug o un UUID en lugar del id numérico. |
| `403 You do not have access to this project` | No hay fila en `user_projects` para ese par usuario/proyecto. |
| `403 Admin access required` | El rol es `Editor` o `Viewer`. |
| `403 Project path param does not match active project scope` | El `{project_id}` del path difiere del header. |
| `400 Invalid catalog code '...'` | El código no existe en la tabla `catalog_*` o tiene `is_active = false`. Suele faltar el seed. |
| `422` con `extra_forbidden` | El payload trae un campo que el schema no declara. |
| El frontend "guarda" pero nada llega al backend | `VITE_API_URL` vacío: `src/lib/api.js` está en modo demo sobre `localStorage`. |

## Trabajar sobre el servicio legacy

`backend/` es un servicio FastAPI separado, con psycopg2 y SQL crudo sobre el
esquema de `db/init.sql`. No comparte modelos ni configuración con `app/`.

Tocalo únicamente para el bootstrap de GeoServer
(`backend/app/geoserver.py`: workspace, datastore y publicación de
featuretypes). Cualquier funcionalidad de producto va en `app/`.

## Antes de cerrar un cambio

1. `python -m pytest -q` y `npm test` en verde.
2. `python scripts/build_repo_graph.py` si agregaste, moviste o borraste
   archivos, endpoints o tablas.
3. Si tocaste una regla de negocio OVI, confirmá que quedó reflejada en los dos
   lados (`app/schemas/observation.py` y `src/components/RightPanel.jsx`).
4. Si agregaste una tabla de negocio, confirmá que tiene `project_id` y que
   todas sus consultas filtran por el proyecto activo.
