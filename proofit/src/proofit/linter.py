"""Orchestrator: parse a runbook draft, run all ten rule checks, collect violations."""
from __future__ import annotations

from .checks import ALL_CHECKS
from .model import LintResult
from .parser import parse


def lint_text(markdown: str) -> LintResult:
    runbook = parse(markdown)
    violations = []
    for check in ALL_CHECKS:
        violations.extend(check(runbook))
    # deterministic order: rule number, then location
    violations.sort(key=lambda v: (v.rule, v.location))
    return LintResult(violations=violations)


def lint_file(path: str) -> LintResult:
    with open(path, encoding="utf-8") as f:
        return lint_text(f.read())
