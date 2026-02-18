# Multi-tenant Row Level Security (RLS)

Este repositorio incluye una migración SQL para activar aislamiento por tenant en PostgreSQL para:

- `public.properties`
- Cualquier otra tabla de `public` que tenga columna `project_id`

## Variables requeridas

- `DATABASE_URL`: cadena de conexión de PostgreSQL.
- `ENABLE_RLS=true`: habilita la ejecución de la migración.

## Cómo aplicar

```bash
ENABLE_RLS=true DATABASE_URL=postgres://user:pass@host:5432/dbname ./scripts/apply_rls.sh
```

Si `ENABLE_RLS` no es `true`, el script no aplica cambios.

## Cómo funciona

1. El script `scripts/apply_rls.sh` valida `ENABLE_RLS`.
2. Si está en `true`, ejecuta `db/migrations/20260218_enable_multi_tenant_rls.sql`.
3. La migración recorre tablas `public.*` con columna `project_id`.
4. Para cada tabla:
   - activa `ENABLE ROW LEVEL SECURITY` y `FORCE ROW LEVEL SECURITY`.
   - crea la política `tenant_isolation`.

La política filtra con:

```sql
project_id::text = current_setting('app.current_project_id', true)
```

Eso aplica tanto a lectura (`USING`) como escritura (`WITH CHECK`).

## Uso en runtime (por request)

Antes de consultar datos, la aplicación debe definir el tenant activo en la sesión:

```sql
SET app.current_project_id = 'project-123';
```

Sin ese valor, `current_setting(..., true)` devuelve `NULL` y la política no expone filas.

## Reversión

Para desactivar RLS y eliminar la política en tablas multi-tenant:

```bash
psql "$DATABASE_URL" -v ON_ERROR_STOP=1 -f db/migrations/20260218_enable_multi_tenant_rls.down.sql
```
