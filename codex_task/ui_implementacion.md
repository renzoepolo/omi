Implementa los cambios de UI/UX acordados:

Requisitos funcionales:
- Header fijo: logo (placeholder), ProjectSelector, UserMenu (dropdown: Administración, Mi perfil, Cerrar sesión).
- El mapa ocupa todo el viewport debajo del header (sin márgenes).
- Cursor de consulta siempre.
- Click en mapa/punto abre panel lateral derecho “Consulta” (drawer) mostrando atributos del punto (read-only).
- FAB abajo derecha con ícono lápiz:
  - Toggle “Modo edición”.
  - Acciones: “Crear punto” y “Editar punto existente”.
- En modo “Crear punto”: click en mapa crea un marcador temporal, abre panel lateral con formulario editable y botón Guardar/Cancelar.
- En modo “Editar punto”: click selecciona un punto existente y habilita edición (mover punto + editar atributos).
- Responsive: en móvil el panel lateral pasa a bottom-sheet.

Restricciones:
- No modificar endpoints ni backend.
- No cambiar nombres de rutas existentes.
- Refactorizar en componentes reutilizables: Header, ProjectSelector, UserMenu, MapView, RightPanel, FAB.

Entrega:
- Código implementado
- Instrucciones para probar local (comandos)

