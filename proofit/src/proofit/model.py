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


@dataclass
class Violation:
    rule: int
    location: str
    message: str
    fix: str

    def render(self) -> str:
        lines = [f"RULE {self.rule} [{self.location}] ERROR \u2014 {self.message}"]
        if self.fix:
            lines.append(f"  fix: {self.fix}")
        return "\n".join(lines)


@dataclass
class LintResult:
    violations: list = field(default_factory=list)  # list[Violation]

    @property
    def passed(self) -> bool:
        return not self.violations
