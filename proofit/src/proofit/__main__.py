"""CLI: python -m proofit lint runbook.md | python -m proofit template

Fail-closed: any violation rejects the draft (exit 1). Clean drafts pass (exit 0).
"""
from __future__ import annotations

import os
import sys

from . import __version__, lint_file


def _template_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "..", "templates", "runbook-template.md"))


def cmd_lint(path: str) -> int:
    try:
        result = lint_file(path)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: cannot read {path}: {e}", file=sys.stderr)
        return 2
    if result.passed:
        print("PASS: no violations — the runbook is locked down.")
        return 0
    for v in result.violations:
        print(v.render())
    n = len(result.violations)
    print(f"\nREJECTED: {n} violation{'s' if n != 1 else ''} — fix and re-run.")
    return 1


def cmd_template() -> int:
    path = _template_path()
    try:
        with open(path, encoding="utf-8") as f:
            sys.stdout.write(f.read())
    except OSError as e:
        print(f"error: template not found at {path}: {e}", file=sys.stderr)
        return 2
    return 0


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if not argv or argv[0] in ("-h", "--help", "help"):
        print(f"proofit {__version__} — fail-closed runbook linter")
        print("usage:")
        print("  python -m proofit lint <runbook.md>   check a draft; exit 1 on any violation")
        print("  python -m proofit template            print the blank runbook template")
        return 0
    if argv[0] == "lint" and len(argv) == 2:
        return cmd_lint(argv[1])
    if argv[0] == "template" and len(argv) == 1:
        return cmd_template()
    print(f"usage: python -m proofit (lint <file> | template)", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
