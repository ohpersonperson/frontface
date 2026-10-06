"""Orchestrator: parse a runbook draft, run all ten rule checks, collect violations.

PARAM-PROOFIT-002: sanctioned, auditable waivers. A draft may carry
`# waiver(<rule>): <reason>` comment lines. A waiver with a stated
reason excuses matching violations (they stay in the record, marked
waived, and do not fail the draft in either mode); a waiver without a
reason is invalid and excuses nothing — fail-closed stays the default.

Operator process, not code: waivers should be reassessed quarterly. A
waiver that was honest three months ago may be a lie today.
"""
from __future__ import annotations

from .checks import ALL_CHECKS
from .model import LintResult, Waiver
from .parser import WAIVER_RE, parse


def parse_waivers(markdown: str) -> list[Waiver]:
    """Collect waiver comments from the draft.

    A waiver is valid only with a non-empty reason. Malformed lines
    (not matching the syntax) are not waivers at all and are ignored;
    matching lines without a reason are invalid waivers — recorded,
    visible, and excusing nothing.
    """
    waivers = []
    for i, line in enumerate(markdown.splitlines(), start=1):
        m = WAIVER_RE.match(line)
        if not m:
            continue
        reason = m.group(2).strip()
        waivers.append(
            Waiver(
                rule=int(m.group(1)),
                reason=reason,
                line_no=i,
                valid=bool(reason),
            )
        )
    return waivers


def lint_text(markdown: str, *, strict: bool = False) -> LintResult:
    runbook = parse(markdown)
    waivers = parse_waivers(markdown)
    violations = []
    for check in ALL_CHECKS:
        violations.extend(check(runbook))
    # deterministic order: rule number, then location
    violations.sort(key=lambda v: (v.rule, v.location))
    # A valid waiver excuses every violation of its rule — in default
    # and --strict mode alike. The violation stays in the record.
    valid = [w for w in waivers if w.valid]
    for v in violations:
        for w in valid:
            if w.rule == v.rule:
                v.waived = True
                v.waiver_reason = w.reason
                break
    return LintResult(violations=violations, waivers=waivers, strict=strict)


def lint_file(path: str, *, strict: bool = False) -> LintResult:
    with open(path, encoding="utf-8") as f:
        return lint_text(f.read(), strict=strict)
