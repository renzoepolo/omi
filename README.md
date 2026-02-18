# OMI GeoServer + PostGIS stack

Implementación en Docker para publicar capas por proyecto en GeoServer y registrar capas base desde backend.

## Servicios incluidos

- **backend**: API FastAPI para gestión de proyectos, propiedades y capas base.
- **db**: PostgreSQL + PostGIS.
- **geoserver**: Publicación OGC (WMS/WFS de solo lectura).
- **nginx**: Reverse proxy de `/api` y `/geoserver`.

## Requisitos implementados

1. **Publicación automática de capa `properties` por proyecto**
   - Se crea una vista `properties_project_<project_id>`.
   - El backend publica automáticamente esa vista como `featureType` en GeoServer al iniciar y al crear nuevos proyectos.

2. **Registro de nuevas capas base desde backend**
   - Endpoint `POST /api/projects/{project_id}/base-layers`:
     - Registra en tabla `base_layers`.
     - Asocia a proyecto en `project_base_layers`.

3. **Sin edición WFS-T**
   - No se implementan endpoints de edición vía WFS-T.
   - La API expone `wfst_enabled: false` en `/api/health`.

4. **docker-compose completo**
   - `backend`, `db`, `geoserver`, `nginx`.

## Levantar entorno

```bash
docker compose up -d --build
```

## Endpoints principales

- `GET /api/health`
- `POST /api/projects`
- `GET /api/projects`
- `POST /api/projects/{project_id}/base-layers`
- `GET /api/projects/{project_id}/base-layers`
- `POST /api/properties`

## Ejemplos rápidos

Crear proyecto:

```bash
curl -X POST http://localhost/api/projects \
  -H 'Content-Type: application/json' \
  -d '{"name":"proyecto-norte"}'
```

Registrar capa base y asociarla al proyecto 1:

```bash
curl -X POST http://localhost/api/projects/1/base-layers \
  -H 'Content-Type: application/json' \
  -d '{
    "name":"OpenStreetMap",
    "service_url":"https://tile.openstreetmap.org/{z}/{x}/{y}.png",
    "layer_type":"xyz"
  }'
```

GeoServer quedará disponible en:

- `http://localhost/geoserver/`
