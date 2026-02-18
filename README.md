# OMI Backend Base

Backend base con FastAPI + SQLAlchemy 2 + PostgreSQL/PostGIS + Alembic + JWT, con aislamiento por proyecto.

## Estructura

```text
app/
  api/
    deps.py
    router.py
    routes/
      auth.py
      projects.py
  core/
    config.py
    database.py
    security.py
  models/
    base.py
    user.py
    project.py
    user_project.py
  schemas/
    auth.py
alembic/
  env.py
  versions/
    20261018_0001_initial_auth_projects.py
scripts/
  seed.py
tests/
  conftest.py
  test_auth_and_isolation.py
```

> **Nota:** No se incluye la tabla `properties` todavía, por solicitud.

## Roles soportados

- `SuperAdmin`
- `ProjectAdmin`
- `Editor`
- `Viewer`

## Levantar local

1. Crear entorno virtual e instalar dependencias:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Configurar variables:

```bash
cp .env.example .env
```

3. Levantar PostgreSQL + PostGIS (ejemplo con Docker):

```bash
docker run --name omi-postgis -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=omi -p 5432:5432 -d postgis/postgis:16-3.4
```

4. Ejecutar migraciones:

```bash
alembic upgrade head
```

5. Cargar seed inicial:

```bash
python -m scripts.seed
```

6. Ejecutar API:

```bash
uvicorn app.main:app --reload
```

## Seed inicial

`python -m scripts.seed` crea:
- Usuarios: `admin@omi.local`, `ana@omi.local`
- Proyectos: `Proyecto A`, `Proyecto B`
- Membresías con roles en `user_projects`

## JWT y aislamiento por proyecto

- Login: `POST /auth/login`
- Middleware obliga `X-Project-Id` en todas las rutas (excepto login/docs/health).
- Dependencia `get_project_membership` valida que el usuario pertenezca al proyecto activo.
- Endpoint ejemplo protegido: `GET /projects/current`

## Tests

```bash
pytest -q
```

Incluye tests de:
- login
- acceso permitido al proyecto asignado
- denegación entre proyectos

## Stack GeoServer + PostGIS (Docker)

Esta rama también incorpora un stack de despliegue con Docker:

- `docker-compose.yml`
- `backend/` (servicio API para integración con GeoServer)
- `db/init.sql`
- `nginx/nginx.conf`

Servicios del stack:
- `backend`
- `db` (PostgreSQL + PostGIS)
- `geoserver`
- `nginx`

Levantar stack:

```bash
docker compose up -d --build
```

## Exportación de proyectos

Incluye exportación con:

- CSV plano (valores codificados)
- CSV interpretado (valores descriptivos)
- GeoPackage (geometría + atributos)

Reglas incluidas:
- Filtro por estado (`statuses`)
- Filtro por rango de fecha (`start_date`, `end_date`)
- Seguridad multi-tenant obligatoria (`tenant_id`)
