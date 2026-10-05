"""Core data model for the proofit runbook linter."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class Step:
    number: int
    name: str
    do: str = ""
    look_for: str = ""
    verify: str = ""
    if_wrong: str = ""
    fix: str = ""
    line_no: int = 0


@dataclass
class ServiceSpec:
    name: str
    body: str = ""
    line_no: int = 0


@dataclass
class Runbook:
    """A runbook draft parsed from Markdown following the proofit template shape."""

    raw: str = ""
    # (kind, title, line_no) for top-level sections, in document order.
    # kind is one of: prereq, steps, validation, glossary, other
    section_order: list = field(default_factory=list)
    prereq_text: str = ""
    prereq_present: bool = False
    steps: list = field(default_factory=list)  # list[Step]
    steps_present: bool = False
    validation_text: str = ""
    validation_present: bool = False
    glossary_text: str = ""
    glossary_present: bool = False
    services: list = field(default_factory=list)  # list[ServiceSpec]


# PARAM-PROOFIT-001: rule -> severity. Structural rules are ERROR
# (fail-closed); heuristic (R1, R8) and convention (R5) are WARNING
# (listed, never fail the draft unless --strict).
ERROR = "ERROR"
WARNING = "WARNING"
SEVERITY_BY_RULE = {
    1: WARNING,   # heuristic: assumptions
    2: ERROR,     # structural: prerequisites
    3: ERROR,     # structural: one action
    4: ERROR,     # structural: concrete refs
    5: WARNING,   # convention: terms
    6: ERROR,     # structural: verification
    7: ERROR,     # structural: recovery
    8: WARNING,   # heuristic: state changes
    9: ERROR,     # structural: routing
    10: ERROR,   # structural: validation
}


@dataclass
class Violation:
    rule: int
    location: str
    message: str
    fix: str
    # Severity is derived from the rule, not passed — the map above is
    # the adjudicated spec. An explicit value wins if ever given.
    severity: str = ""

    def __post_init__(self) -> None:
        if not self.severity:
            self.severity = SEVERITY_BY_RULE.get(self.rule, ERROR)

    def render(self) -> str:
        lines = [f"RULE {self.rule} [{self.location}] {self.severity} \u2014 {self.message}"]
        if self.fix:
            lines.append(f"  fix: {self.fix}")
        return "\n".join(lines)


@dataclass
class LintResult:
    violations: list = field(default_factory=list)  # list[Violation]
    # PARAM-PROOFIT-001: strict mode restores the old fail-on-anything
    # behavior (the --strict CLI flag). Default is fail-closed on ERRORs.
    strict: bool = False

    @property
    def errors(self) -> list:
        return [v for v in self.violations if v.severity == ERROR]

    @property
    def warnings(self) -> list:
        return [v for v in self.violations if v.severity == WARNING]

    @property
    def passed(self) -> bool:
        if self.strict:
            return not self.violations
        return not self.errors
