# OMI — Observatorio del Mercado Inmobiliario

Visor de mapa multi-proyecto donde se cargan y consultan **observaciones** de
valor de inmuebles, más un panel de administración de usuarios, proyectos y
capas de GeoServer.

## Empezá por el grafo del repositorio

Antes de buscar a ciegas, consultá la documentación de arquitectura. Está
generada desde el código y se mantiene sincronizada con él:

- **[`docs/architecture/README.md`](docs/architecture/README.md)** — índice y
  cómo consultar el grafo.
- [`docs/architecture/01-system-map.md`](docs/architecture/01-system-map.md) —
  servicios, despliegue y configuración.
- [`docs/architecture/02-request-flows.md`](docs/architecture/02-request-flows.md) —
  cómo viaja un request de punta a punta.
- [`docs/architecture/03-domain-invariants.md`](docs/architecture/03-domain-invariants.md) —
  **reglas que no se pueden romper**. Leelo antes de tocar `app/` o `src/lib/api.js`.
- [`docs/architecture/04-agent-playbooks.md`](docs/architecture/04-agent-playbooks.md) —
  recetas paso a paso para los cambios frecuentes.
- [`docs/architecture/repo-graph.json`](docs/architecture/repo-graph.json) — el
  grafo completo en formato máquina: archivos, imports, endpoints y tablas.

`docs/architecture/generated/` contiene el grafo de módulos, el diagrama ER y
la lista de endpoints. **Son archivos generados: no los edites a mano.**

## Comandos

```bash
# Backend (Python 3.11, FastAPI)
source .venv/bin/activate
alembic upgrade head          # esquema
python -m scripts.seed        # datos de ejemplo
uvicorn app.main:app --reload # http://localhost:8000
python -m pytest -q           # 36 tests, SQLite en memoria

# Frontend (React 18 + Vite)
npm run dev                   # http://localhost:5173
npm test                      # vitest
npm run lint

# Documentación
python scripts/build_repo_graph.py          # regenerar el grafo
python scripts/build_repo_graph.py --check  # verificar que está al día

# Stack completo
docker compose -f docker-compose.app.yml up --build   # visor en :8500
```

## Reglas del proyecto

1. **Hay dos backends.** `app/` es el backend actual (FastAPI + SQLAlchemy +
   Alembic, modelo de observaciones). `backend/` es un servicio anterior sobre
   la tabla `properties` con SQL crudo, cuyo único valor vigente es el
   bootstrap de GeoServer. Toda funcionalidad de producto va en `app/`.

2. **El proyecto es el tenant.** Todo request lleva el header `X-Project-Id`
   numérico salvo las rutas de `PROJECT_ID_EXEMPT_PATHS` en `app/main.py`. El
   scope nunca sale del body ni del path: se valida contra `user_projects`.
   Toda tabla de negocio nueva necesita `project_id` y toda consulta debe
   filtrar por el proyecto activo.

3. **`shared/ovi_enums.json` es la única fuente de verdad de los códigos OVI.**
   Lo consumen el backend (`app/core/ovi_enums.py`) y el frontend
   (`src/components/RightPanel.jsx`). Nunca hardcodees un código OVI en Python
   ni en JSX.

4. **Las reglas de negocio OVI están duplicadas a propósito**, en
   `app/schemas/observation.py` (`validate_business_rules`) y en
   `src/components/RightPanel.jsx` (`isOviUrbanoBaldioValid`). Si cambiás una,
   cambiá la otra.

5. **El borrado es lógico.** `DELETE` marca `status = eliminado` y setea
   `deleted_at`; la fila nunca se borra. Todo cambio de estado escribe en
   `observation_status_history`.

6. **Los endpoints de `/admin` que mutan datos llaman a `_audit`.** Es lo único
   que alimenta `admin_audit_logs`.

7. **Regenerá el grafo** con `python scripts/build_repo_graph.py` cuando un
   cambio agregue, mueva o borre archivos, endpoints o tablas, y commiteá el
   resultado junto al cambio.

## Cosas que sorprenden

- **La geometría no está en PostGIS.** Las coordenadas de una observación viven
  en el JSONB `observations.extras.coordinates` como `[lon, lat]`. No hay
  columna `geom` en `app/models/`.
- **RLS está definido pero no conectado.** La política de
  `db/migrations/20260218_enable_multi_tenant_rls.sql` compara contra
  `current_setting('app.current_project_id')`, variable que el backend nunca
  setea. Activar RLS hoy dejaría las consultas en cero filas.
- **Un `Viewer` puede escribir observaciones por API.** Las rutas de
  observaciones sólo exigen pertenencia al proyecto, no rol. El frontend oculta
  la UI de edición, pero eso no es una restricción de seguridad.
- **`savePoints` reenvía todos los puntos en cada guardado**, no sólo el
  editado: un request por punto más un refetch.
- **Con `VITE_API_URL` vacío el frontend entra en modo demo** y guarda todo en
  `localStorage` sin tocar la API.
- **Los tests del backend corren sobre SQLite en memoria**, así que no validan
  JSONB, RLS ni nada específico de PostgreSQL.

## Idioma

El código y los identificadores están en inglés, salvo los campos del
diccionario OVI, que conservan sus nombres originales en mayúsculas
(`VALOR_TOTAL`, `FECHA_VALOR`, `NOMENCLATURA`). La documentación y los mensajes
de la interfaz están en español.
