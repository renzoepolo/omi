Implementa sección de administración (backend) con endpoints protegidos:

Roles:
- Solo SuperAdmin y ProjectAdmin acceden a admin (ProjectAdmin solo para su proyecto).

Funcionalidades:
1) Proyectos (CRUD):
   - name, description
   - default_map_center (lng, lat), default_zoom
   - default_base_layers (referencias a layers)
   - form configuration (relación con form_field_definitions)
2) Capas base por proyecto:
   - Tabla layers: name, geoserver_workspace, geoserver_layer_name, type (WMS/WFS), default_visible, z_index
   - Tabla project_layers: project_id + layer_id + overrides (visible, z_index)
   - Endpoint: asociar/desasociar capas a proyecto
3) Usuarios:
   - CRUD usuarios
   - Asignación a proyectos (user_projects) + rol por proyecto
   - Auditoría de cambios (ip + user-agent)

Entrega:
- Migraciones
- Tests de permisos admin
- Seeds de ejemplo

