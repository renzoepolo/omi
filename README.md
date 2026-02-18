# Exportación de proyectos

Implementación de exportación con:

1. CSV plano (valores codificados)
2. CSV interpretado (valores descriptivos)
3. GeoPackage (geometría + atributos)

## Reglas incluidas

- Filtro por estado (`statuses`)
- Filtro por rango de fecha (`start_date`, `end_date`)
- Seguridad multi-tenant obligatoria (`tenant_id` requerido y aplicado en todos los exportes)

## Uso rápido

```python
import datetime as dt
from exporter import ProjectExporter, ProjectRecord

records = [
    ProjectRecord(
        id=1,
        tenant_id="tenant-a",
        status_code="active",
        created_at=dt.date(2025, 1, 10),
        project_type_code="INFRA",
        name="Proyecto A",
        latitude=19.43,
        longitude=-99.13,
    )
]

exporter = ProjectExporter(records)
exporter.export_csv_plano("out/plano.csv", tenant_id="tenant-a")
exporter.export_csv_interpretado("out/interpretado.csv", tenant_id="tenant-a")
exporter.export_geopackage("out/proyectos.gpkg", tenant_id="tenant-a")
```
