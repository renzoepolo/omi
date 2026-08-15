# Mapa del sistema

## Servicios

```mermaid
graph TB
  subgraph browser["Navegador"]
    SPA["SPA React + MapLibre<br/>src/"]
  end

  subgraph edge["Nginx (docker/frontend-nginx.conf)"]
    NGINX["Sirve el build estático<br/>proxy /api/ y /geoserver/"]
  end

  subgraph api["Backend FastAPI — app/"]
    MW["Middleware X-Project-Id<br/>app/main.py"]
    ROUTES["Routers: auth, projects,<br/>observations, admin"]
    ORM["SQLAlchemy 2.0 + Alembic"]
  end

  GS["GeoServer 2.25.2<br/>capas WMS/WFS"]
  DB[("PostgreSQL 16 + PostGIS")]

  LEGACY["Servicio legacy — backend/<br/>bootstrap de GeoServer"]

  SPA -->|"fetch /api/*"| NGINX
  SPA -->|"tiles WMS /geoserver/*"| NGINX
  NGINX --> MW
  NGINX --> GS
  MW --> ROUTES
  ROUTES --> ORM
  ORM --> DB
  ROUTES -->|"REST admin<br/>httpx"| GS
  LEGACY --> DB
  LEGACY --> GS
```

## Piezas y responsabilidades

| Pieza | Ruta | Stack | Responsabilidad |
| --- | --- | --- | --- |
| SPA | `src/` | React 18, Vite 5, MapLibre GL 4, Tailwind, Radix UI | Visor de mapa, alta/edición de observaciones y panel de administración. |
| Backend | `app/` | FastAPI, SQLAlchemy 2.0, Alembic, python-jose, passlib | API REST, autenticación JWT, aislamiento por proyecto, proxy de lectura a GeoServer. |
| Base de datos | `alembic/versions/` | PostgreSQL 16 + PostGIS | Persistencia. El esquema real lo definen las migraciones de Alembic. |
| GeoServer | contenedor | GeoServer 2.25.2 | Publica capas base y temáticas que el visor consume por WMS. |
| Nginx | `docker/frontend-nginx.conf` | nginx 1.27 | Sirve el SPA y hace de único origen: `/api/` → backend, `/geoserver/` → GeoServer. |
| Servicio legacy | `backend/` | FastAPI, psycopg2, requests | Stack anterior: crea el workspace/datastore de GeoServer y publica vistas `properties_project_{id}`. **No comparte modelos con `app/`.** |

## Frontera importante: hay dos backends

El repositorio contiene dos servicios FastAPI distintos y es fácil confundirlos:

- **`app/`** es el backend actual. Trabaja sobre el modelo de observaciones,
  usa SQLAlchemy y Alembic, y es el que construyen `Dockerfile.backend`,
  `docker-compose.app.yml` y `docker-compose.full.yml`.
- **`backend/`** es un servicio anterior sobre la tabla `properties` de
  `db/init.sql`, con SQL crudo vía psycopg2. Sólo lo levanta
  `docker-compose.yml`. Su valor vigente es el bootstrap de GeoServer en
  `backend/app/geoserver.py`.

**Al implementar una funcionalidad de producto, el destino es `app/`.** Tocar
`backend/` sólo tiene sentido para la publicación de capas en GeoServer.

## Stacks de Docker Compose

| Archivo | Levanta | Cuándo usarlo |
| --- | --- | --- |
| `docker-compose.app.yml` | db + geoserver + backend (`app/`) + frontend | Stack completo actual. El frontend queda en `localhost:8500`. |
| `docker-compose.full.yml` | db + backend (`app/`) + frontend | Igual pero sin GeoServer, para trabajar sólo sobre la API y el visor. |
| `docker-compose.yml` | db + geoserver + backend legacy + nginx | Stack antiguo, ligado a `backend/` y `db/init.sql`. |
| `deploy/docker-compose.production.yml` | app + nginx con TLS | Plantilla de producción; ver `deploy/docs/production-hardening.md`. |

El arranque del backend está en `docker/backend-entrypoint.sh`: espera a la
base, corre `alembic upgrade head`, ejecuta `python -m scripts.seed` y recién
entonces levanta uvicorn. Es decir, **las migraciones y el seed corren solos en
Docker**; en desarrollo local hay que ejecutarlos a mano.

## Configuración

El backend lee su configuración con `pydantic-settings` en `app/core/config.py`
desde variables de entorno o `.env`:

| Variable | Default | Uso |
| --- | --- | --- |
| `SECRET_KEY` | `change-me` | Firma de los JWT. |
| `DATABASE_URL` | `postgresql+psycopg://postgres:postgres@localhost:5432/omi` | Conexión SQLAlchemy (driver `psycopg` v3). |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | Vigencia del token. |
| `GEOSERVER_URL` / `GEOSERVER_USER` / `GEOSERVER_PASSWORD` | `localhost:8080`, `admin`, `geoserver` | Endpoints `/admin/geoserver/*`. |

El frontend usa dos variables de build de Vite:

- `VITE_API_URL` — base de la API. **Si está vacía, `src/lib/api.js` entra en
  modo demo**: login contra un usuario hardcodeado, proyectos ficticios y
  puntos guardados en `localStorage`. El panel de admin no funciona en ese
  modo.
- `VITE_GEOSERVER_URL` — base para armar las URLs WMS de las capas temáticas
  en `src/components/MapView.jsx`.

## Geometría: dónde vive realmente

Las observaciones **no** usan PostGIS. La coordenada de cada punto se guarda
como par `[lon, lat]` dentro del JSONB `observations.extras.coordinates`
(escrito en `src/lib/api.js` y leído en el mismo archivo para reconstruir el
GeoJSON del mapa). No existe columna `geom` en `app/models/`.

PostGIS sí se usa en el esquema legacy `db/init.sql`, para la tabla
`properties` que consume el servicio `backend/`.

Consecuencia práctica: hoy no se pueden hacer consultas espaciales sobre
observaciones desde SQL. Migrar `extras.coordinates` a una columna
`geometry(Point, 4326)` es un cambio pendiente de diseño, no un detalle de
implementación.
