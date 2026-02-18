-- psql variable expected:
--   -v app_enable_rls=true|false
SELECT set_config('app.enable_rls', COALESCE(:'app_enable_rls', 'false'), false);

DO $$
DECLARE
  is_enabled boolean := lower(COALESCE(current_setting('app.enable_rls', true), 'false')) = 'true';
  target_table record;
BEGIN
  IF NOT is_enabled THEN
    RAISE NOTICE 'RLS disabled (app.enable_rls != true). No changes were applied.';
    RETURN;
  END IF;

  FOR target_table IN
    SELECT n.nspname AS schema_name, c.relname AS table_name
    FROM pg_class c
    INNER JOIN pg_namespace n ON n.oid = c.relnamespace
    INNER JOIN pg_attribute a ON a.attrelid = c.oid
    WHERE c.relkind = 'r'
      AND n.nspname = 'public'
      AND a.attname = 'project_id'
      AND a.attnum > 0
      AND NOT a.attisdropped
  LOOP
    EXECUTE format('ALTER TABLE %I.%I ENABLE ROW LEVEL SECURITY', target_table.schema_name, target_table.table_name);
    EXECUTE format('ALTER TABLE %I.%I FORCE ROW LEVEL SECURITY', target_table.schema_name, target_table.table_name);

    EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I.%I', target_table.schema_name, target_table.table_name);
    EXECUTE format(
      'CREATE POLICY tenant_isolation ON %I.%I USING (project_id::text = current_setting(''app.current_project_id'', true)) WITH CHECK (project_id::text = current_setting(''app.current_project_id'', true))',
      target_table.schema_name,
      target_table.table_name
    );
  END LOOP;

  IF NOT EXISTS (
    SELECT 1
    FROM pg_class c
    INNER JOIN pg_namespace n ON n.oid = c.relnamespace
    WHERE c.relname = 'properties' AND n.nspname = 'public'
  ) THEN
    RAISE NOTICE 'Table public.properties was not found. Multi-tenant RLS was applied to every table with project_id.';
  END IF;
END
$$;
