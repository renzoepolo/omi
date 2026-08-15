#!/usr/bin/env bash
#
# Corre los linters SOLO sobre los archivos modificados respecto de la rama base.
#
# El repositorio arrastra deuda de estilo previa (al escribir esto, 89 hallazgos
# de ruff, 67 de ellos lineas largas). Bloquear todo de golpe habria significado
# un diff mecanico enorme, asi que el gate es progresivo: lo que tocas, queda
# limpio.
#
# Uso:
#   scripts/lint_changed.sh py     # ruff check + ruff format --check
#   scripts/lint_changed.sh js     # eslint + prettier --check
#   scripts/lint_changed.sh all    # ambos (por defecto)
#
# La rama base se toma de BASE_REF, o se deduce (origin/main, luego main).
#
# Esta logica vive en un script y no dentro del YAML de CI a proposito: asi el
# gate local y el de CI no pueden desincronizarse.

set -euo pipefail

target="${1:-all}"
repo_root="$(git rev-parse --show-toplevel)"
cd "$repo_root"

resolve_base() {
  if [ -n "${BASE_REF:-}" ]; then
    printf '%s' "$BASE_REF"
    return
  fi
  # main local primero: es la rama de integracion. origin/main puede estar
  # atrasada y meter ruido de commits ya integrados localmente.
  for candidate in main origin/main; do
    if git rev-parse --verify --quiet "$candidate" >/dev/null 2>&1; then
      printf '%s' "$candidate"
      return
    fi
  done
  printf ''
}

base="$(resolve_base)"

# $1 = regex de extensiones, $2 = --diff-filter de git.
#   ACMR -> archivos tocados (agregados, copiados, modificados, renombrados)
#   A    -> solo archivos nuevos
_files() {
  local pattern="$1"
  local filter="$2"
  {
    if [ -n "$base" ]; then
      local merge_base
      merge_base="$(git merge-base "$base" HEAD 2>/dev/null || true)"
      if [ -n "$merge_base" ]; then
        git diff --name-only --diff-filter="$filter" "$merge_base" HEAD
      fi
    fi
    git diff --name-only --diff-filter="$filter" HEAD
    git ls-files --others --exclude-standard
  } | { grep -E "$pattern" || true; } \
    | { grep -vE '^(alembic/versions/|dist/|node_modules/|\.venv/)' || true; } \
    | sort -u | while IFS= read -r file; do
    [ -f "$file" ] && printf '%s\n' "$file"
  done
}

changed_files() { _files "$1" ACMR; }

# El chequeo de formato aplica solo a archivos nuevos: los existentes nunca
# pasaron por prettier y arrastrarlos al gate por tocarles una linea produce
# diffs mecanicos de cientos de lineas que tapan el cambio real. Los archivos
# viejos se van formateando cuando se reescriben, con `npm run format`.
new_files() { _files "$1" A; }

status=0

lint_py() {
  local files=()
  while IFS= read -r file; do files+=("$file"); done < <(changed_files '\.py$')

  if [ ${#files[@]} -eq 0 ]; then
    echo "[py] sin archivos modificados"
    return 0
  fi

  echo "[py] ${#files[@]} archivo(s) a revisar:"
  printf '  %s\n' "${files[@]}"

  # --force-exclude hace que ruff respete el exclude de pyproject.toml incluso
  # cuando los archivos se pasan explicitamente (ej. alembic/versions).
  ruff check --force-exclude -- "${files[@]}" || status=1

  local fresh=()
  while IFS= read -r file; do fresh+=("$file"); done < <(new_files '\.py$')
  if [ ${#fresh[@]} -gt 0 ]; then
    ruff format --check --force-exclude -- "${fresh[@]}" || status=1
  fi
}

lint_js() {
  local files=()
  while IFS= read -r file; do files+=("$file"); done < <(changed_files '\.(js|jsx)$')

  if [ ${#files[@]} -eq 0 ]; then
    echo "[js] sin archivos modificados"
    return 0
  fi

  echo "[js] ${#files[@]} archivo(s) a revisar:"
  printf '  %s\n' "${files[@]}"

  npx --no-install eslint --no-warn-ignored -- "${files[@]}" || status=1

  local fresh=()
  while IFS= read -r file; do fresh+=("$file"); done < <(new_files '\.(js|jsx)$')
  if [ ${#fresh[@]} -gt 0 ]; then
    npx --no-install prettier --check --ignore-unknown -- "${fresh[@]}" || status=1
  fi
}

case "$target" in
  py) lint_py ;;
  js) lint_js ;;
  all)
    lint_py
    lint_js
    ;;
  *)
    echo "Uso: $0 [py|js|all]" >&2
    exit 2
    ;;
esac

if [ "$status" -ne 0 ]; then
  echo ""
  echo "Hay hallazgos en archivos que tocaste. Arreglos automaticos:"
  echo "  ruff check --fix . && ruff format .    # Python"
  echo "  npm run format                          # JS/JSX"
fi

exit "$status"
