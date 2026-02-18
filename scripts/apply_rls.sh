#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${DATABASE_URL:-}" ]]; then
  echo "DATABASE_URL is required"
  exit 1
fi

ENABLE_RLS_VALUE="${ENABLE_RLS:-false}"
if [[ "${ENABLE_RLS_VALUE,,}" != "true" ]]; then
  echo "ENABLE_RLS is not true. Skipping RLS migration."
  exit 0
fi

psql "$DATABASE_URL" \
  -v ON_ERROR_STOP=1 \
  -v app_enable_rls="$ENABLE_RLS_VALUE" \
  -f db/migrations/20260218_enable_multi_tenant_rls.sql

echo "RLS migration applied with ENABLE_RLS=$ENABLE_RLS_VALUE"
