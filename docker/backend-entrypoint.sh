#!/usr/bin/env sh
set -eu

echo "Waiting for database..."
for i in $(seq 1 60); do
  if python -c "import os, psycopg; dsn=os.environ['DATABASE_URL'].replace('postgresql+psycopg://','postgresql://',1); psycopg.connect(dsn, connect_timeout=2).close()" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "Running migrations..."
alembic upgrade head

echo "Seeding initial data..."
python -m scripts.seed

echo "Starting API..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
