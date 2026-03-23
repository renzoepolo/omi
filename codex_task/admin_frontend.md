Implementa UI de administración accesible desde el dropdown del usuario:

- Ruta /admin (solo SuperAdmin/ProjectAdmin)
- Pantallas:
  1) Proyectos: lista + crear/editar (centro mapa: permite “centrar mapa actual y guardar”, zoom, nombre)
  2) Capas por proyecto: checklist + orden (drag/drop opcional) + visible por defecto
  3) Campos del formulario por proyecto: editor de form_field_definitions (orden, requerido, visible por tipo_inmueble, valores codificados)
  4) Usuarios: lista + asignar proyectos + roles

Restricciones:
- UI rápida, moderna, minimalista.
- No romper el visor: el admin abre como página/overlay separado.

Entrega:
- Código + rutas
- Confirmar responsive mínimo

