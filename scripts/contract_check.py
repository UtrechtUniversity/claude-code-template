#!/usr/bin/env python3
"""Contract check: verify frontend API calls match backend routes.

Parses backend FastAPI route declarations and frontend fetch() calls,
then reports mismatches:

  [frontend_orphan] METHOD PATH  — frontend calls it; no backend route (HARD FAILURE)
  [backend_orphan]  METHOD PATH  — backend route exists; frontend never uses (WARN)

Exit code 1 on any frontend orphan, 0 otherwise.

This script is the cross-side defense against multi-agent endpoint drift:
one agent renames a route, another agent's frontend keeps the old name,
both sides' unit tests pass, the wired-up flow fails. Run on every
non-docs PR.

Run from the repo root:
    python3 scripts/contract_check.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Path normalisation: collapse {id} / ${id} / :id to a shared wildcard token
# so /items/{id} matches /items/${id}.
# ---------------------------------------------------------------------------

_PARAM_RE = re.compile(
    r"\{[^}]+\}"                          # FastAPI {param}
    r"|\$\{[^}]+\}"                       # JS template-literal ${param}
    r"|:[A-Za-z_][A-Za-z0-9_]*(?=/|$)"    # Express-style :param
)
_QUERY_RE = re.compile(r"\?.*$")
WILDCARD = "{*}"


def _normalise_path(path: str) -> str:
    path = _QUERY_RE.sub("", path)
    path = _PARAM_RE.sub(WILDCARD, path)
    # Collapse double slashes (except leading) and strip trailing slash so
    # /items and /items/ are treated the same. The route table prints
    # without trailing slash; both sides use the normalised form.
    path = re.sub(r"(?<!^)//+", "/", path)
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]
    return path


# ---------------------------------------------------------------------------
# Backend parser
# ---------------------------------------------------------------------------

_ROUTER_PREFIX_RE = re.compile(
    r"include_router\(\s*([A-Za-z_][A-Za-z0-9_]*)"
    r"[^)]*prefix\s*=\s*[\"']([^\"']*)[\"']",
    re.DOTALL,
)
_ROUTER_NAME_RE = re.compile(
    r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=\s*APIRouter\b",
    re.MULTILINE,
)
_ROUTER_IMPORT_RE = re.compile(
    r"from\s+([A-Za-z_][A-Za-z0-9_.]*)\s+import\s+([A-Za-z_][A-Za-z0-9_]*)"
    r"(?:\s+as\s+([A-Za-z_][A-Za-z0-9_]*))?",
)
_DECORATOR_RE = re.compile(
    r"^\s*@(?P<obj>router|app)\.(?P<method>get|post|put|patch|delete|head|options)"
    r"\s*\(\s*[\"'](?P<path>[^\"']*)[\"']",
    re.MULTILINE | re.IGNORECASE,
)


def parse_backend_routes(src_dir: Path) -> list[tuple[str, str]]:
    """Return (METHOD, normalised_path) tuples for every backend route.

    Walks every .py file under *src_dir*. For each file:
      - Decorators on `app` (typically in main.py) contribute directly.
      - Decorators on `router` contribute under the prefix that main.py
        mounts the router with (via include_router(name, prefix=...)).
    """
    routes: list[tuple[str, str]] = []

    main_file = src_dir / "main.py"
    main_source = main_file.read_text(encoding="utf-8") if main_file.is_file() else ""

    # Map: module path → mount prefix from include_router(name, prefix=...).
    # We resolve the *name* back to the file that defines `name = APIRouter()`
    # via the from-imports in main.py.
    mounts = _resolve_router_mounts(main_source)

    for py_file in sorted(src_dir.rglob("*.py")):
        if py_file.name == "__init__.py":
            continue
        source = py_file.read_text(encoding="utf-8")
        # Find which mount prefix (if any) applies to this file. We look
        # at the `name = APIRouter()` assignment and check if main.py
        # imported that name (under any alias) and mounted it.
        prefix = ""
        for name_match in _ROUTER_NAME_RE.finditer(source):
            local_name = name_match.group(1)
            module_path = _module_path(src_dir, py_file)
            prefix = mounts.get((module_path, local_name), prefix)

        for m in _DECORATOR_RE.finditer(source):
            obj = m.group("obj")
            method = m.group("method").upper()
            raw = m.group("path")
            # Only apply prefix to @router decorators. @app decorators
            # (typically in main.py) already carry the full path.
            full = (prefix + raw) if obj == "router" else raw
            routes.append((method, _normalise_path(full)))

    return routes


def _module_path(src_dir: Path, py_file: Path) -> str:
    rel = py_file.relative_to(src_dir.parent).with_suffix("")
    return ".".join(rel.parts)


def _resolve_router_mounts(main_source: str) -> dict[tuple[str, str], str]:
    """From main.py source, build a map (module_dotted, local_name) → prefix.

    Resolves both `from app.routes.items import router as items_router`
    and `from app.routes.items import router` patterns.
    """
    imports: dict[str, tuple[str, str]] = {}
    for m in _ROUTER_IMPORT_RE.finditer(main_source):
        module, name, alias = m.group(1), m.group(2), m.group(3)
        bound = alias or name
        imports[bound] = (module, name)

    mounts: dict[tuple[str, str], str] = {}
    for m in _ROUTER_PREFIX_RE.finditer(main_source):
        bound, prefix = m.group(1), m.group(2)
        if bound in imports:
            module, original = imports[bound]
            mounts[(module, original)] = prefix
    return mounts


# ---------------------------------------------------------------------------
# Frontend parser
# ---------------------------------------------------------------------------

# Two call shapes are supported:
#   fetch("/path"[, opts])             — direct fetch
#   request<T>("/path"[, opts])        — typed helper wrapping fetch
# In both cases the path may be a plain string or a template literal,
# and an optional options object may carry a method:"METHOD" key
# (default GET).
_CALL_RE = re.compile(
    r"""(?:fetch|request)\s*(?:<[^>]*>)?\s*\(\s*
    (?:
        ["'](?P<plain>/[^"']*)["']           # "/api/items/"
        |`(?P<tmpl>/[^`]*)`                  # `/api/items/${id}`
    )
    (?:\s*,\s*(?P<opts>\{[^}]*\}))?
    """,
    re.VERBOSE | re.DOTALL,
)
_METHOD_RE = re.compile(r'method\s*:\s*["\']([A-Z]+)["\']', re.IGNORECASE)


def parse_frontend_calls(src_dir: Path) -> list[tuple[str, str]]:
    """Walk every .ts and .svelte file under *src_dir* for fetch / request calls.

    Test files are ignored. Tests are mocked, not contracts.
    """
    calls: list[tuple[str, str]] = []
    for f in sorted([*src_dir.rglob("*.ts"), *src_dir.rglob("*.svelte")]):
        if "/tests/" in str(f) or f.name.endswith(".test.ts"):
            continue
        source = f.read_text(encoding="utf-8")
        for m in _CALL_RE.finditer(source):
            raw = m.group("plain") or m.group("tmpl")
            opts = m.group("opts") or ""
            method_match = _METHOD_RE.search(opts)
            method = method_match.group(1).upper() if method_match else "GET"
            calls.append((method, _normalise_path(raw)))
    return calls


# ---------------------------------------------------------------------------
# Compare + report
# ---------------------------------------------------------------------------


def main(repo_root: Path | None = None) -> int:
    if repo_root is None:
        repo_root = Path(__file__).resolve().parents[1]

    backend_src = repo_root / "backend" / "src" / "app"
    frontend_src = repo_root / "frontend" / "src"

    if not backend_src.is_dir():
        print(f"ERROR: backend source not found: {backend_src}", file=sys.stderr)
        return 2
    if not frontend_src.is_dir():
        print(f"ERROR: frontend source not found: {frontend_src}", file=sys.stderr)
        return 2

    backend = sorted(set(parse_backend_routes(backend_src)))
    frontend = sorted(set(parse_frontend_calls(frontend_src)))

    print("=" * 60)
    print("BACKEND ROUTES")
    print("=" * 60)
    for method, path in backend:
        print(f"  {method:8s} {path}")

    print()
    print("=" * 60)
    print("FRONTEND CALLS")
    print("=" * 60)
    for method, path in frontend:
        print(f"  {method:8s} {path}")

    backend_set = set(backend)
    frontend_set = set(frontend)
    frontend_orphans = sorted(frontend_set - backend_set)
    backend_orphans = sorted(backend_set - frontend_set)

    print()
    print("=" * 60)
    print("VIOLATIONS")
    print("=" * 60)

    if frontend_orphans:
        print("FRONTEND ORPHANS (frontend calls a route that has no backend handler):")
        for method, path in frontend_orphans:
            print(f"  [frontend_orphan] {method} {path}")
    else:
        print("No frontend orphans.")

    if backend_orphans:
        print()
        print("BACKEND ORPHANS (backend route with no frontend caller) [informational]:")
        for method, path in backend_orphans:
            print(f"  [backend_orphan]  {method} {path}")
    else:
        print("No backend orphans.")

    print()
    print("=" * 60)
    print(
        f"Summary: {len(backend)} backend routes, {len(frontend)} frontend calls, "
        f"{len(frontend_orphans)} frontend orphan(s)."
    )
    if frontend_orphans:
        print("RESULT: FAIL — frontend orphan(s) detected.")
        return 1
    print("RESULT: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
