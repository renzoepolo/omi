"""Construye el grafo de conocimiento del repositorio OMI.

Recorre el código fuente y produce artefactos que describen el repositorio como
un grafo (nodos = archivos/módulos/tablas/endpoints, aristas = imports y claves
foráneas). El objetivo es doble:

1. Dar a los agentes de IA un índice navegable y verificable del repositorio
   (`docs/architecture/repo-graph.json`), en vez de obligarlos a redescubrir la
   estructura con búsquedas ciegas en cada sesión.
2. Mantener la documentación de arquitectura sincronizada con el código: los
   archivos bajo `docs/architecture/generated/` se regeneran desde el código y
   nunca deben editarse a mano.

Uso:

    python scripts/build_repo_graph.py            # regenera los artefactos
    python scripts/build_repo_graph.py --check    # falla si están desactualizados

Sólo usa la biblioteca estándar, así que corre sin instalar dependencias.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "docs" / "architecture"
GENERATED_DIR = OUT_DIR / "generated"

EXCLUDED_DIRS = {
    ".git",
    ".claude",
    ".venv",
    ".pytest_cache",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
}

PY_SUFFIXES = {".py"}
JS_SUFFIXES = {".js", ".jsx"}
# Assets que el código importa directamente y que por lo tanto son nodos del
# grafo: el contrato de enums compartido y las hojas de estilo del visor.
ASSET_GLOBS = ("shared/*.json", "src/styles/*.css")

# Prefijos de módulo que se consideran internos al repositorio.
INTERNAL_PY_ROOTS = {"app", "scripts", "tests", "backend", "alembic"}

# Clasificación de cada archivo en una capa arquitectónica. Se evalúa en orden y
# gana el primer prefijo que coincide, así que van de más específico a más general.
LAYER_RULES: list[tuple[str, str]] = [
    ("app/api/routes", "backend-routes"),
    ("app/api", "backend-api"),
    ("app/core", "backend-core"),
    ("app/models", "backend-models"),
    ("app/schemas", "backend-schemas"),
    ("app/main.py", "backend-entrypoint"),
    ("alembic/versions", "migrations"),
    ("alembic", "migrations"),
    ("db/migrations", "migrations-sql"),
    ("db", "migrations-sql"),
    ("backend", "legacy-geoserver-service"),
    ("src/components/ui", "frontend-ui-kit"),
    ("src/components", "frontend-components"),
    ("src/lib", "frontend-lib"),
    ("src/styles", "frontend-styles"),
    ("src", "frontend-entrypoint"),
    ("shared", "shared-contract"),
    ("scripts", "scripts"),
    ("tests", "tests"),
    ("deploy", "deploy"),
    ("docker", "deploy"),
    ("nginx", "deploy"),
]


def classify_layer(rel_path: str) -> str:
    for prefix, layer in LAYER_RULES:
        if rel_path == prefix or rel_path.startswith(prefix + "/"):
            return layer
    return "root"


@dataclass
class Node:
    id: str
    kind: str
    layer: str
    loc: int
    exports: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "kind": self.kind,
            "layer": self.layer,
            "loc": self.loc,
            "exports": sorted(self.exports),
        }


@dataclass
class Route:
    method: str
    path: str
    handler: str
    source: str
    tags: list[str]

    def to_dict(self) -> dict:
        return {
            "method": self.method,
            "path": self.path,
            "handler": self.handler,
            "source": self.source,
            "tags": self.tags,
        }


@dataclass
class Table:
    name: str
    model: str
    source: str
    columns: list[str]
    primary_key: list[str]
    foreign_keys: list[tuple[str, str]]  # (columna, tabla.columna destino)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "model": self.model,
            "source": self.source,
            "columns": self.columns,
            "primary_key": self.primary_key,
            "foreign_keys": [
                {"column": column, "references": target} for column, target in self.foreign_keys
            ],
        }


def iter_source_files() -> list[Path]:
    files: list[Path] = []
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.relative_to(ROOT).parts):
            continue
        if path.suffix in PY_SUFFIXES | JS_SUFFIXES:
            files.append(path)
    return sorted(files)


def iter_asset_files() -> list[Path]:
    files: list[Path] = []
    for pattern in ASSET_GLOBS:
        files.extend(path for path in ROOT.glob(pattern) if path.is_file())
    return sorted(files)


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


# --------------------------------------------------------------------------- #
# Análisis de Python
# --------------------------------------------------------------------------- #


def module_name_for(rel_path: str) -> str:
    module = rel_path[: -len(".py")]
    if module.endswith("/__init__"):
        module = module[: -len("/__init__")]
    return module.replace("/", ".")


def python_module_index(py_files: list[Path]) -> dict[str, str]:
    """Mapa nombre_de_módulo -> ruta relativa, para resolver imports internos."""
    index: dict[str, str] = {}
    for path in py_files:
        index[module_name_for(rel(path))] = rel(path)
    return index


def resolve_python_import(module: str, index: dict[str, str]) -> str | None:
    if not module:
        return None
    if module.split(".")[0] not in INTERNAL_PY_ROOTS:
        return None
    # Un import puede apuntar a un módulo o a un símbolo dentro de un módulo.
    candidate = module
    while candidate:
        if candidate in index:
            return index[candidate]
        if "." not in candidate:
            return None
        candidate = candidate.rsplit(".", 1)[0]
    return None


def analyze_python(path: Path, index: dict[str, str]) -> tuple[Node, list[str], list[Route], list[Table]]:
    rel_path = rel(path)
    source = path.read_text(encoding="utf-8")
    loc = source.count("\n") + 1
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return Node(rel_path, "python", classify_layer(rel_path), loc), [], [], []

    imports: set[str] = set()
    exports: list[str] = []
    routes: list[Route] = []
    tables: list[Table] = []

    # Routers declarados a nivel de módulo: nombre_variable -> (prefix, tags)
    routers: dict[str, tuple[str, list[str]]] = {}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = resolve_python_import(alias.name, index)
                if target and target != rel_path:
                    imports.add(target)
        elif isinstance(node, ast.ImportFrom):
            if node.level:  # import relativo
                base = rel_path.rsplit("/", 1)[0].replace("/", ".")
                parts = base.split(".")
                if node.level > 1:
                    parts = parts[: -(node.level - 1)] or parts
                module = ".".join(parts + ([node.module] if node.module else []))
            else:
                module = node.module or ""
            target = resolve_python_import(module, index)
            if target and target != rel_path:
                imports.add(target)
            elif node.module and node.module.split(".")[0] in INTERNAL_PY_ROOTS:
                for alias in node.names:
                    target = resolve_python_import(f"{node.module}.{alias.name}", index)
                    if target and target != rel_path:
                        imports.add(target)

    for node in tree.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    exports.append(target.id)
                    router_info = _router_declaration(node.value)
                    if router_info is not None:
                        routers[target.id] = router_info
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            exports.append(node.name)

    routes.extend(_collect_routes(tree, routers, rel_path))
    tables.extend(_collect_tables(tree, rel_path))

    return (
        Node(rel_path, "python", classify_layer(rel_path), loc, exports),
        sorted(imports),
        routes,
        tables,
    )


def _router_declaration(value: ast.expr) -> tuple[str, list[str]] | None:
    if not isinstance(value, ast.Call):
        return None
    func = value.func
    name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
    if name not in {"APIRouter", "FastAPI"}:
        return None
    prefix = ""
    tags: list[str] = []
    for keyword in value.keywords:
        if keyword.arg == "prefix" and isinstance(keyword.value, ast.Constant):
            prefix = str(keyword.value.value)
        if keyword.arg == "tags" and isinstance(keyword.value, ast.List):
            tags = [
                str(element.value)
                for element in keyword.value.elts
                if isinstance(element, ast.Constant)
            ]
    return prefix, tags


HTTP_METHODS = {"get", "post", "put", "patch", "delete", "head", "options"}


def _collect_routes(tree: ast.Module, routers: dict[str, tuple[str, list[str]]], source: str) -> list[Route]:
    routes: list[Route] = []
    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for decorator in node.decorator_list:
            if not isinstance(decorator, ast.Call):
                continue
            func = decorator.func
            if not isinstance(func, ast.Attribute) or func.attr not in HTTP_METHODS:
                continue
            if not isinstance(func.value, ast.Name):
                continue
            router_name = func.value.id
            if router_name not in routers:
                continue
            prefix, tags = routers[router_name]
            path_arg = ""
            if decorator.args and isinstance(decorator.args[0], ast.Constant):
                path_arg = str(decorator.args[0].value)
            routes.append(
                Route(
                    method=func.attr.upper(),
                    path=(prefix + path_arg) or "/",
                    handler=node.name,
                    source=source,
                    tags=tags,
                )
            )
    return routes


def _collect_tables(tree: ast.Module, source: str) -> list[Table]:
    tables: list[Table] = []
    for node in tree.body:
        if not isinstance(node, ast.ClassDef):
            continue
        base_names = {base.id for base in node.bases if isinstance(base, ast.Name)}
        if "Base" not in base_names:
            continue

        table_name = ""
        columns: list[str] = []
        primary_key: list[str] = []
        foreign_keys: list[tuple[str, str]] = []

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name) and target.id == "__tablename__":
                        if isinstance(item.value, ast.Constant):
                            table_name = str(item.value.value)
            if not isinstance(item, ast.AnnAssign) or not isinstance(item.target, ast.Name):
                continue
            column_name = item.target.id
            if column_name.startswith("__"):
                continue
            call = item.value
            if not isinstance(call, ast.Call):
                continue
            call_name = getattr(call.func, "id", getattr(call.func, "attr", ""))
            if call_name == "relationship":
                continue
            columns.append(column_name)
            for keyword in call.keywords:
                if (
                    keyword.arg == "primary_key"
                    and isinstance(keyword.value, ast.Constant)
                    and keyword.value.value is True
                ):
                    primary_key.append(column_name)
            for sub in ast.walk(call):
                if (
                    isinstance(sub, ast.Call)
                    and getattr(sub.func, "id", "") == "ForeignKey"
                    and sub.args
                    and isinstance(sub.args[0], ast.Constant)
                ):
                    foreign_keys.append((column_name, str(sub.args[0].value)))

        if table_name:
            tables.append(
                Table(
                    name=table_name,
                    model=node.name,
                    source=source,
                    columns=columns,
                    primary_key=primary_key,
                    foreign_keys=foreign_keys,
                )
            )
    return tables


# --------------------------------------------------------------------------- #
# Análisis de JavaScript / JSX
# --------------------------------------------------------------------------- #

JS_IMPORT_RE = re.compile(
    r"""(?:^|\n)\s*(?:import\s[^'"\n]*?from\s*|import\s*|export\s[^'"\n]*?from\s*)['"]([^'"]+)['"]""",
)
JS_EXPORT_RE = re.compile(
    r"""^\s*export\s+(?:default\s+)?(?:async\s+)?(?:function|const|class|let)\s+([A-Za-z0-9_$]+)""",
    re.MULTILINE,
)


def resolve_js_import(spec: str, importer: Path) -> str | None:
    if not spec.startswith("."):
        return None
    base = (importer.parent / spec).resolve()
    candidates = [base]
    candidates += [base.with_suffix(suffix) for suffix in (".js", ".jsx", ".json", ".css")]
    candidates += [base / f"index{suffix}" for suffix in (".js", ".jsx")]
    for candidate in candidates:
        if candidate.is_file():
            try:
                return rel(candidate)
            except ValueError:
                return None
    return None


def analyze_js(path: Path) -> tuple[Node, list[str]]:
    rel_path = rel(path)
    source = path.read_text(encoding="utf-8")
    loc = source.count("\n") + 1
    imports: set[str] = set()
    for match in JS_IMPORT_RE.finditer(source):
        target = resolve_js_import(match.group(1), path)
        if target and target != rel_path:
            imports.add(target)
    exports = JS_EXPORT_RE.findall(source)
    if re.search(r"^\s*export\s+default\s+function\s*\(", source, re.MULTILINE):
        exports.append("default")
    kind = "jsx" if path.suffix == ".jsx" else "javascript"
    return Node(rel_path, kind, classify_layer(rel_path), loc, exports), sorted(imports)


# --------------------------------------------------------------------------- #
# Construcción del grafo
# --------------------------------------------------------------------------- #


def build_graph() -> dict:
    files = iter_source_files()
    py_files = [f for f in files if f.suffix in PY_SUFFIXES]
    js_files = [f for f in files if f.suffix in JS_SUFFIXES]
    index = python_module_index(py_files)

    nodes: list[Node] = []
    edges: list[dict] = []
    routes: list[Route] = []
    tables: list[Table] = []

    for path in py_files:
        node, imports, file_routes, file_tables = analyze_python(path, index)
        nodes.append(node)
        edges.extend({"from": node.id, "to": target, "kind": "imports"} for target in imports)
        routes.extend(file_routes)
        tables.extend(file_tables)

    for path in js_files:
        node, imports = analyze_js(path)
        nodes.append(node)
        edges.extend({"from": node.id, "to": target, "kind": "imports"} for target in imports)

    for path in iter_asset_files():
        rel_path = rel(path)
        loc = path.read_text(encoding="utf-8").count("\n") + 1
        nodes.append(Node(rel_path, "asset", classify_layer(rel_path), loc))

    # Un import que no cae en un nodo conocido (una dependencia de npm resuelta
    # por casualidad, por ejemplo) sería una arista colgante y rompería el grafo.
    known = {node.id for node in nodes}
    edges = [edge for edge in edges if edge["from"] in known and edge["to"] in known]

    tables_by_name = {table.name: table for table in tables}
    for table in tables:
        for column, target in table.foreign_keys:
            target_table = target.split(".")[0]
            if target_table in tables_by_name:
                edges.append(
                    {
                        "from": table.name,
                        "to": target_table,
                        "kind": "foreign_key",
                        "via": column,
                    }
                )

    layers: dict[str, list[str]] = {}
    for node in nodes:
        layers.setdefault(node.layer, []).append(node.id)

    return {
        "generated_by": "scripts/build_repo_graph.py",
        "note": "Archivo generado. No editar a mano; regenerar con `python scripts/build_repo_graph.py`.",
        "stats": {
            "files": len(nodes),
            "import_edges": sum(1 for edge in edges if edge["kind"] == "imports"),
            "routes": len(routes),
            "tables": len(tables),
            "loc": sum(node.loc for node in nodes),
        },
        "layers": {layer: sorted(paths) for layer, paths in sorted(layers.items())},
        "nodes": [node.to_dict() for node in sorted(nodes, key=lambda n: n.id)],
        "edges": sorted(
            edges, key=lambda edge: (edge["kind"], edge["from"], edge["to"])
        ),
        "routes": [route.to_dict() for route in sorted(routes, key=lambda r: (r.source, r.path, r.method))],
        "tables": [table.to_dict() for table in sorted(tables, key=lambda t: t.name)],
    }


# --------------------------------------------------------------------------- #
# Renderizado a Markdown + Mermaid
# --------------------------------------------------------------------------- #

HEADER = "<!-- GENERADO POR scripts/build_repo_graph.py — NO EDITAR A MANO -->\n"

LAYER_LABELS = {
    "backend-entrypoint": "Backend · entrypoint",
    "backend-api": "Backend · API (deps/router)",
    "backend-routes": "Backend · rutas",
    "backend-core": "Backend · core",
    "backend-models": "Backend · modelos",
    "backend-schemas": "Backend · schemas",
    "frontend-entrypoint": "Frontend · entrypoint",
    "frontend-components": "Frontend · componentes",
    "frontend-ui-kit": "Frontend · UI kit",
    "frontend-lib": "Frontend · lib",
    "frontend-styles": "Frontend · estilos",
    "shared-contract": "Contrato compartido",
    "migrations": "Migraciones (Alembic)",
    "migrations-sql": "Migraciones (SQL)",
    "legacy-geoserver-service": "Servicio GeoServer (legacy)",
    "scripts": "Scripts",
    "tests": "Tests",
    "deploy": "Deploy",
    "root": "Raíz",
}

# Capas cuyo grafo de imports se dibuja en el diagrama de módulos. Se excluyen
# tests y migraciones porque inflan el diagrama sin aportar estructura.
GRAPH_LAYERS = {
    "backend-entrypoint",
    "backend-api",
    "backend-routes",
    "backend-core",
    "backend-models",
    "backend-schemas",
    "frontend-entrypoint",
    "frontend-components",
    "frontend-lib",
    "shared-contract",
    "scripts",
}


def mermaid_id(path: str) -> str:
    return re.sub(r"[^A-Za-z0-9]", "_", path)


def render_module_graph(graph: dict) -> str:
    nodes = {node["id"]: node for node in graph["nodes"]}
    visible = {
        node_id
        for node_id, node in nodes.items()
        if node["layer"] in GRAPH_LAYERS and not node_id.endswith("__init__.py")
    }

    by_layer: dict[str, list[str]] = {}
    for node_id in sorted(visible):
        by_layer.setdefault(nodes[node_id]["layer"], []).append(node_id)

    lines = [
        HEADER,
        "# Grafo de módulos\n",
        "Aristas = imports reales extraídos del código fuente.",
        "Se omiten tests, migraciones y `__init__.py` para que el diagrama sea legible.\n",
        "```mermaid",
        "graph LR",
    ]

    ordered_layers = [layer for layer in LAYER_LABELS if layer in by_layer]
    for layer in ordered_layers:
        lines.append(f'  subgraph {mermaid_id(layer)}["{LAYER_LABELS[layer]}"]')
        for node_id in by_layer[layer]:
            label = node_id.split("/")[-1]
            lines.append(f'    {mermaid_id(node_id)}["{label}"]')
        lines.append("  end")

    for edge in graph["edges"]:
        if edge["kind"] != "imports":
            continue
        if edge["from"] in visible and edge["to"] in visible:
            lines.append(f'  {mermaid_id(edge["from"])} --> {mermaid_id(edge["to"])}')

    lines.append("```\n")

    lines.append("## Archivos por capa\n")
    for layer in [key for key in LAYER_LABELS if key in graph["layers"]]:
        lines.append(f"### {LAYER_LABELS[layer]}\n")
        for node_id in graph["layers"][layer]:
            node = nodes[node_id]
            lines.append(f"- `{node_id}` — {node['loc']} líneas")
        lines.append("")

    return "\n".join(lines)


def render_data_model(graph: dict) -> str:
    lines = [
        HEADER,
        "# Modelo de datos\n",
        "Entidades derivadas de los modelos SQLAlchemy en `app/models/`.",
        "Las relaciones son claves foráneas declaradas en el código.\n",
        "```mermaid",
        "erDiagram",
    ]

    for table in graph["tables"]:
        lines.append(f"  {table['name']} {{")
        pk = set(table["primary_key"])
        fk = {item["column"] for item in table["foreign_keys"]}
        for column in table["columns"]:
            marker = "PK" if column in pk else ("FK" if column in fk else "")
            lines.append(f"    col {column} {marker}".rstrip())
        lines.append("  }")

    table_names = {table["name"] for table in graph["tables"]}
    for table in graph["tables"]:
        for item in table["foreign_keys"]:
            target = item["references"].split(".")[0]
            if target not in table_names:
                continue
            # Si la FK es además toda la clave primaria del hijo, la relación es
            # 1:1 (así están modeladas las tablas de detalle de observación).
            is_one_to_one = table["primary_key"] == [item["column"]]
            cardinality = "||--||" if is_one_to_one else "||--o{"
            lines.append(f'  {target} {cardinality} {table["name"]} : "{item["column"]}"')

    lines.append("```\n")

    lines.append("## Tablas\n")
    lines.append("| Tabla | Modelo | Archivo | Columnas |")
    lines.append("| --- | --- | --- | --- |")
    for table in graph["tables"]:
        lines.append(
            f"| `{table['name']}` | `{table['model']}` | `{table['source']}` | {len(table['columns'])} |"
        )
    lines.append("")
    return "\n".join(lines)


def render_api_surface(graph: dict) -> str:
    lines = [
        HEADER,
        "# Superficie de API\n",
        "Endpoints extraídos de los decoradores FastAPI. El prefijo de cada router",
        "ya viene aplicado.\n",
    ]

    by_source: dict[str, list[dict]] = {}
    for route in graph["routes"]:
        by_source.setdefault(route["source"], []).append(route)

    for source in sorted(by_source):
        lines.append(f"## `{source}`\n")
        lines.append("| Método | Ruta | Handler |")
        lines.append("| --- | --- | --- |")
        for route in by_source[source]:
            lines.append(f"| `{route['method']}` | `{route['path']}` | `{route['handler']}` |")
        lines.append("")

    return "\n".join(lines)


def write_outputs(graph: dict) -> dict[Path, str]:
    return {
        OUT_DIR / "repo-graph.json": json.dumps(graph, indent=2, ensure_ascii=False) + "\n",
        GENERATED_DIR / "module-graph.md": render_module_graph(graph),
        GENERATED_DIR / "data-model.md": render_data_model(graph),
        GENERATED_DIR / "api-surface.md": render_api_surface(graph),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="No escribe nada; devuelve código 1 si los artefactos están desactualizados.",
    )
    args = parser.parse_args()

    graph = build_graph()
    outputs = write_outputs(graph)

    if args.check:
        stale = [
            path
            for path, content in outputs.items()
            if not path.exists() or path.read_text(encoding="utf-8") != content
        ]
        if stale:
            for path in stale:
                print(f"desactualizado: {path.relative_to(ROOT)}", file=sys.stderr)
            print(
                "Ejecutá `python scripts/build_repo_graph.py` y commiteá el resultado.",
                file=sys.stderr,
            )
            return 1
        print("El grafo del repositorio está actualizado.")
        return 0

    GENERATED_DIR.mkdir(parents=True, exist_ok=True)
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
        print(f"escrito: {path.relative_to(ROOT)}")

    stats = graph["stats"]
    print(
        f"{stats['files']} archivos, {stats['import_edges']} imports, "
        f"{stats['routes']} endpoints, {stats['tables']} tablas."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
