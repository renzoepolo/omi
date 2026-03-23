Implementa estas nuevas features para el panel de administración:

- Mejorar experiencia de usuario. Debe leerse de manera correcta, corregir separaciones, margenes, etc.
- Sección "Proyectos" 
	- Eliminar lista de proyectos. El proyecto activo para edición es el que aparece en el selector del header.
- Seccion Capas: 
	- Muestra el listado de capas actuales y permite ordenarlas (arrastrándolas). El orden de aparición condiciona el orden del panel de capas del visor (la capa de observaciones siempre es la primera en el panel de capa, esa no es configurable y los mapas base las últimas)
	- Catalogo de capas: Muestras las capas disponibles en el workspace de geoserver. Modificar geoserver para separar por workspaces aislados
	- Incorporar siempre como WMS, seleccionar estilos disponibles.
	- Campos: Reemplazar la etiqueta "Key" por "Nombre de campo", "Label" por "Alias". Permitir arrastarlos para configurar el orden de aparición. Acomodar las etiquetas "Visible por tipo_inmueble" y "Valores codificados reemplazarlo como para que se vea como una tabla"

Entrega:
- Cambios en backend y frontend
- Tests mínimos actualizados
