# Arquitectura de OMI — documentación como grafo

OMI es un observatorio del mercado inmobiliario: un visor de mapa donde
usuarios de distintos proyectos (tenants) cargan y consultan **observaciones**
de valor de inmuebles, más un panel de administración para gestionar usuarios,
proyectos y capas de GeoServer.

Esta carpeta describe el repositorio como un grafo navegable. Está pensada
tanto para personas como para agentes de IA: en vez de redescubrir la
estructura del proyecto con búsquedas ciegas en cada sesión, se entra por acá.

## Cómo leer esta documentación

| Documento | Qué responde |
| --- | --- |
| [`01-system-map.md`](01-system-map.md) | Qué servicios existen, cómo se despliegan y cómo se hablan entre sí. |
| [`02-request-flows.md`](02-request-flows.md) | Cómo viaja un request de punta a punta (login, alta de observación, admin). |
| [`03-domain-invariants.md`](03-domain-invariants.md) | Reglas que **no** se pueden romper: multi-tenancy, contrato OVI, estados. |
| [`04-agent-playbooks.md`](04-agent-playbooks.md) | Recetas paso a paso para las tareas de cambio más frecuentes. |
| [`generated/module-graph.md`](generated/module-graph.md) | Grafo de imports reales entre archivos, por capa. |
| [`generated/data-model.md`](generated/data-model.md) | Diagrama ER derivado de los modelos SQLAlchemy. |
| [`generated/api-surface.md`](generated/api-surface.md) | Todos los endpoints FastAPI con su ruta completa. |
| [`repo-graph.json`](repo-graph.json) | El grafo completo en formato máquina. |

Además, [`ovi_diseno_tecnico.md`](../ovi_diseno_tecnico.md) es el documento de
diseño original del modelo OVI: explica *por qué* el modelo quedó como quedó.
Cuando el diseño y el código difieren, **manda el código**; el diseño describe
un estado objetivo del que todavía falta implementar parte.

## El grafo del repositorio

`repo-graph.json` se genera desde el código con:

```bash
python scripts/build_repo_graph.py
```

No necesita dependencias: usa sólo la biblioteca estándar. El script parsea el
AST de los archivos Python y los `import` de los archivos JS/JSX, y produce:

- **`nodes`** — cada archivo fuente con su capa arquitectónica, cantidad de
  líneas y símbolos exportados.
- **`edges`** — aristas `imports` (archivo → archivo) y `foreign_key`
  (tabla → tabla).
- **`routes`** — cada endpoint FastAPI con método, ruta completa y handler.
- **`tables`** — cada tabla con sus columnas, clave primaria y claves foráneas.
- **`layers`** — índice inverso: qué archivos componen cada capa.

Los archivos bajo `generated/` se derivan del mismo grafo y **no deben editarse
a mano**: cualquier cambio se pierde en la siguiente regeneración. Para
verificar que están sincronizados con el código (útil en CI o antes de un
commit):

```bash
python scripts/build_repo_graph.py --check
```

Devuelve código de salida 1 si algo quedó desactualizado.

### Consultar el grafo sin leer todo el repositorio

El formato JSON está pensado para responder preguntas puntuales sin abrir
decenas de archivos. Algunos ejemplos:

```bash
# ¿Qué archivos dependen de app/models/observation.py?
python -c "import json;g=json.load(open('docs/architecture/repo-graph.json'));\
print([e['from'] for e in g['edges'] if e['to']=='app/models/observation.py'])"

# ¿Qué endpoints toca el router de admin?
python -c "import json;g=json.load(open('docs/architecture/repo-graph.json'));\
print([r['path'] for r in g['routes'] if 'admin' in r['source']])"

# ¿Qué tablas apuntan a projects?
python -c "import json;g=json.load(open('docs/architecture/repo-graph.json'));\
print([e['from'] for e in g['edges'] if e['kind']=='foreign_key' and e['to']=='projects'])"
```

## Regla de mantenimiento

Si un cambio agrega o mueve archivos, endpoints o tablas, hay que regenerar el
grafo y commitear el resultado junto al cambio. Es una sola línea y mantiene
honesta a toda la documentación derivada.
