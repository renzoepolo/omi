DO $$
DECLARE
  target_table record;
BEGIN
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
    EXECUTE format('DROP POLICY IF EXISTS tenant_isolation ON %I.%I', target_table.schema_name, target_table.table_name);
    EXECUTE format('ALTER TABLE %I.%I NO FORCE ROW LEVEL SECURITY', target_table.schema_name, target_table.table_name);
    EXECUTE format('ALTER TABLE %I.%I DISABLE ROW LEVEL SECURITY', target_table.schema_name, target_table.table_name);
  END LOOP;
END
$$;
