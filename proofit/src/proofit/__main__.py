"""CLI: python -m proofit lint runbook.md | python -m proofit template

Fail-closed on ERRORs: any structural violation rejects the draft (exit 1).
WARNINGs (heuristic/convention rules) are listed but don't fail the draft —
unless --strict is passed, which restores fail-on-anything.
"""
from __future__ import annotations

import os
import sys

from . import __version__, lint_file
from .ledger import Ledger


def _template_path() -> str:
    here = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(here, "..", "..", "templates", "runbook-template.md"))


def cmd_lint(path: str, *, strict: bool = False) -> int:
    try:
        result = lint_file(path, strict=strict)
    except FileNotFoundError:
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2
    except OSError as e:
        print(f"error: cannot read {path}: {e}", file=sys.stderr)
        return 2
    _record_lint(path, result)
    print(result.render())
    if not result.passed:
        # active errors, or (strict mode and active violations)
        n = len(result.active_violations)
        print(f"\nREJECTED: {n} violation{'s' if n != 1 else ''} — fix and re-run.")
        return 1
    valid_waivers = [w for w in result.waivers if w.valid]
    if valid_waivers:
        print(f"\nWAIVERS: {len(valid_waivers)} valid waiver"
              f"{'s' if len(valid_waivers) != 1 else ''} applied — "
              "waived violations are excused, not erased.")
    if result.warnings:
        n = len(result.warnings)
        print(f"\nWARNINGS: {n} warning{'s' if n != 1 else ''} — pass "
              f"(warnings don't fail the draft; use --strict to fail on them).")
        return 0
    print("PASS: no violations — the runbook is locked down.")
    return 0


def _record_lint(path: str, result) -> None:
    """Append one lint record. Digest of the draft, never the draft."""
    try:
        with open(path, encoding="utf-8") as f:
            content = f.read()
    except OSError:
        content = None
    by_rule: dict[int, int] = {}
    for v in result.violations:
        by_rule[v.rule] = by_rule.get(v.rule, 0) + 1
    Ledger("proofit").record(
        "lint",
        {
            "passed": result.passed,
            "violations": len(result.violations),
            "by_rule": by_rule,
            # Waiver metadata only — never the reason text (the ledger
            # stores digests of draft content, never the content).
            "waivers": len(result.waivers),
            "waivers_valid": sum(1 for w in result.waivers if w.valid),
            "waived_violations": sum(1 for v in result.violations if v.waived),
        },
        input_text=content,
    )


def cmd_ledger(argv: list[str]) -> int:
    led = Ledger("proofit")
    s = led.summary()
    print(f"proofit ledger: {s['records']} records "
          f"({led.path})")
    for ev, n in sorted(s["events"].items()):
        print(f"  {ev}: {n}")
    if s["records"]:
        print(f"  first: {s['first']}")
        print(f"  last:  {s['last']}")
        try:
            limit = int(argv[0]) if argv else 5
        except ValueError:
            limit = 5
        print(f"  recent {limit}:")
        for r in led.read(limit=limit):
            sm = r["summary"]
            print(f"    {r['ts']} lint "
                  f"passed={sm['passed']} violations={sm['violations']} "
                  f"by_rule={sm['by_rule']}")
    return 0


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
        print("  python -m proofit lint [--strict] <runbook.md>")
        print("      check a draft; ERRORs reject (exit 1), WARNINGs pass unless --strict")
        print("  python -m proofit template            print the blank runbook template")
        print("  python -m proofit ledger [n]          show the local lint ledger (last n, default 5)")
        return 0
    if argv[0] == "lint" and len(argv) in (2, 3):
        args = argv[1:]
        strict = "--strict" in args
        paths = [a for a in args if a != "--strict"]
        if len(paths) != 1:
            print("usage: python -m proofit lint [--strict] <runbook.md>",
                  file=sys.stderr)
            return 2
        return cmd_lint(paths[0], strict=strict)
    if argv[0] == "template" and len(argv) == 1:
        return cmd_template()
    if argv[0] == "ledger":
        return cmd_ledger(argv[1:])
    print(f"usage: python -m proofit (lint <file> | template | ledger [n])", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
