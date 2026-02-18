CREATE EXTENSION IF NOT EXISTS postgis;

CREATE TABLE IF NOT EXISTS projects (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS properties (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    code TEXT NOT NULL,
    owner_name TEXT,
    geom geometry(Point, 4326) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS base_layers (
    id SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    service_url TEXT NOT NULL,
    layer_type TEXT NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    UNIQUE(name, service_url, layer_type)
);

CREATE TABLE IF NOT EXISTS project_base_layers (
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    base_layer_id INTEGER NOT NULL REFERENCES base_layers(id) ON DELETE CASCADE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY(project_id, base_layer_id)
);

INSERT INTO projects(name)
VALUES ('default')
ON CONFLICT (name) DO NOTHING;

INSERT INTO properties(project_id, code, owner_name, geom)
SELECT p.id, 'PROP-001', 'Owner demo', ST_SetSRID(ST_MakePoint(-70.66, -33.45), 4326)
FROM projects p
WHERE p.name = 'default'
AND NOT EXISTS (
    SELECT 1 FROM properties pr WHERE pr.code = 'PROP-001' AND pr.project_id = p.id
);
