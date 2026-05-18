#!/usr/bin/env python3
"""Pre-commit check: fail when a staged Python file's NET doc growth exceeds NET code growth.

Per issue #239: agents (especially Opus) write long paraphrase docstrings next to small
code changes. The paraphrases drift from source-of-truth docs and the next agent reads the
closest comment first. The check uses *net* deltas (added - removed) so docstring
rewrites and cleanups don't trip; only genuine doc growth that outpaces code change does.

Usage: python3 .githooks/check_comment_density.py <staged_py_path> [<staged_py_path> ...]
Exits 1 on violation, 0 otherwise.
"""

from __future__ import annotations

import ast
import subprocess
import sys


def _doc_line_set(src: str) -> set[int]:
    doc: set[int] = set()
    for i, line in enumerate(src.splitlines(), start=1):
        if line.lstrip().startswith("#"):
            doc.add(i)
    try:
        tree = ast.parse(src)
    except SyntaxError:
        return doc
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        body = getattr(node, "body", None)
        if not body or not isinstance(body[0], ast.Expr):
            continue
        v = body[0].value
        if isinstance(v, ast.Constant) and isinstance(v.value, str) and v.end_lineno is not None:
            for ln in range(v.lineno, v.end_lineno + 1):
                doc.add(ln)
    return doc


def _read_pre_image(path: str) -> str | None:
    out = subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if out.returncode != 0:
        return None
    return out.stdout


def _read_post_image(path: str) -> str | None:
    out = subprocess.run(
        ["git", "show", f":{path}"],
        capture_output=True,
        text=True,
        check=False,
    )
    if out.returncode != 0:
        return None
    return out.stdout


def _changed_lines(path: str) -> tuple[set[int], set[int]]:
    out = subprocess.run(
        ["git", "diff", "--cached", "-U0", "--", path],
        capture_output=True,
        text=True,
        check=False,
    ).stdout
    added: set[int] = set()
    removed: set[int] = set()
    new_ln = 0
    old_ln = 0
    for line in out.splitlines():
        if line.startswith("@@"):
            try:
                old_part = line.split("-", 1)[1].split(" ", 1)[0]
                old_ln = int(old_part.split(",", 1)[0])
                new_part = line.split("+", 1)[1].split(" ", 1)[0]
                new_ln = int(new_part.split(",", 1)[0])
            except (IndexError, ValueError):
                pass
            continue
        if line.startswith("+++") or line.startswith("---"):
            continue
        if line.startswith("+"):
            added.add(new_ln)
            new_ln += 1
        elif line.startswith("-"):
            removed.add(old_ln)
            old_ln += 1
    return added, removed


def _classify(line_numbers: set[int], src: str | None) -> tuple[int, int]:
    if src is None:
        return 0, 0
    doc = _doc_line_set(src)
    lines = src.splitlines()
    docs = 0
    code = 0
    for ln in line_numbers:
        if ln < 1 or ln > len(lines):
            continue
        if not lines[ln - 1].strip():
            continue
        if ln in doc:
            docs += 1
        else:
            code += 1
    return docs, code


def main(paths: list[str]) -> int:
    violations: list[tuple[str, int, int]] = []
    for path in paths:
        added, removed = _changed_lines(path)
        if not added and not removed:
            continue
        post = _read_post_image(path)
        pre = _read_pre_image(path)
        added_doc, added_code = _classify(added, post)
        removed_doc, removed_code = _classify(removed, pre)
        net_doc = added_doc - removed_doc
        net_code = added_code - removed_code
        if net_doc > net_code and net_doc > 5:
            violations.append((path, net_doc, net_code))
    if violations:
        print()
        print("  pre-commit: comment-density check failed (issue #239).")
        print("  Net doc/comment growth exceeds code growth in a staged Python file.")
        print("  Agents tend to paraphrase reference docs; the paraphrases drift over time.")
        print()
        for path, net_doc, net_code in violations:
            print(f"    {path}: net +{net_doc} doc lines, net +{net_code} code lines")
        print()
        print("  Either trim the prose, or split into a docs-only commit if intentional.")
        print()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
