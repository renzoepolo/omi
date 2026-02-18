# OMI Frontend (React + Vite + MapLibre GL)

Aplicación frontend para:

- Login con JWT.
- Selector de proyecto.
- Visualización de capa `properties` vía GeoServer WMS + capas base.
- CRUD de puntos (crear, mover, editar atributos y cambiar estado).
- Simbología por estado.
- Diseño responsive para móvil.

## Variables de entorno

Crea un archivo `.env` opcional:

```bash
VITE_API_URL=http://localhost:8000/api
VITE_GEOSERVER_WMS=http://localhost:8080/geoserver/wms
VITE_GEOSERVER_LAYER=workspace:properties
```

Si `VITE_API_URL` no está definido, la app usa modo demo local con:

- usuario: `admin`
- contraseña: `admin123`

## Scripts

```bash
npm install
npm run dev
npm run build
```
