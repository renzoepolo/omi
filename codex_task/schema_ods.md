Necesito implementar el esquema real de la tabla de observaciones (puntos) basado en el archivo:

Diccionario de datos_Tabla OVI_v2.ods

Reglas:
- Ignorar columnas: longitud, precisión y estado_carga.
- La geometría es Point EPSG:4326.
- Mantener status del flujo: cargado, posicionado, revision, completado, outlier, eliminado.
- price es numérico + requiere campo moneda.
- El formulario debe soportar “tipo_inmueble” (urbano_baldio, urbano_edificado, rural) y ocultar/deshabilitar campos según tipo (esto se controla con configuración administrable).

Tareas:
1) Lee el ODS y lista los campos finales a implementar (nombre, tipo, valores permitidos).
2) Decide qué va como columna fija y qué va en JSONB (si aplica) JUSTIFICANDO.
3) Implementa:
   - Modelo SQLAlchemy
   - Migración Alembic
   - Schemas Pydantic
   - Validaciones (valores permitidos)
4) Actualiza:
   - Plantilla CSV de descarga
   - Importador CSV
   - Export CSV plano + interpretado
   - Export GeoPackage
   - UI: panel de consulta y panel de edición para mostrar esos campos

Entrega:
- Cambios en backend y frontend
- Tests mínimos actualizados
- Comandos para validar (pytest + docker compose)

