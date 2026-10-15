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
# (fail-closed); heuristic (R1, R8, R13) and convention (R5) are WARNING
# (listed, never fail the draft unless --strict).
# The 1337 module (R11, R12, R14) is fail-closed ERROR; R13's cute-length
# namesake is half joke, half real, so it reports as heuristic WARNING.
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
    11: ERROR,    # 1337 module: cross-role duplication
    12: ERROR,    # 1337 module: header date check
    13: WARNING,  # 1337 module: suspicious character count (namesake)
    14: ERROR,    # 1337 module: missing-file verification
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
    # PARAM-PROOFIT-002: sanctioned waiver. A waived violation stays in
    # the record (visible, with its reason) but does not fail the draft.
    waived: bool = False
    waiver_reason: str = ""

    def __post_init__(self) -> None:
        if not self.severity:
            self.severity = SEVERITY_BY_RULE.get(self.rule, ERROR)

    def render(self) -> str:
        lines = [f"RULE {self.rule} [{self.location}] {self.severity} \u2014 {self.message}"]
        if self.fix:
            lines.append(f"  fix: {self.fix}")
        if self.waived:
            lines.append(f"  waived: {self.waiver_reason}")
        return "\n".join(lines)


@dataclass
class Waiver:
    """One `# waiver(<rule>): <reason>` comment from the draft.

    A waiver is valid only with a stated reason — no reason, no waiver
    (fail-closed stays the default). Valid waivers excuse matching
    violations without removing them from the record.

    Operator process, not code: waivers should be reassessed quarterly.
    A waiver that made sense three months ago may be a lie today —
    the reassessment is the operator's job; this class only records.
    """

    rule: int
    reason: str
    line_no: int = 0
    valid: bool = False

    def render(self) -> str:
        if self.valid:
            return (
                f"WAIVER rule {self.rule} (line {self.line_no}): "
                f"{self.reason}"
            )
        return (
            f"WAIVER rule {self.rule} (line {self.line_no}): "
            "INVALID — no reason given; does not excuse."
        )


@dataclass
class LintResult:
    violations: list = field(default_factory=list)  # list[Violation]
    waivers: list = field(default_factory=list)  # list[Waiver]
    # PARAM-PROOFIT-001: strict mode restores the old fail-on-anything
    # behavior (the --strict CLI flag). Default is fail-closed on ERRORs.
    # PARAM-PROOFIT-002: waived violations fail in NEITHER mode.
    strict: bool = False

    @property
    def active_violations(self) -> list:
        """Violations not covered by a valid waiver — the ones that count."""
        return [v for v in self.violations if not v.waived]

    @property
    def errors(self) -> list:
        return [v for v in self.active_violations if v.severity == ERROR]

    @property
    def warnings(self) -> list:
        return [v for v in self.active_violations if v.severity == WARNING]

    @property
    def passed(self) -> bool:
        if self.strict:
            return not self.active_violations
        return not self.errors

    def render(self) -> str:
        """The full lint record: violations (waived or not) plus waivers.

        Waived violations stay visible here with their reasons — the
        waiver excuses, it never erases.
        """
        lines = []
        for v in self.violations:
            lines.append(v.render())
        for w in self.waivers:
            lines.append(w.render())
        return "\n".join(lines)
