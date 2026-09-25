"""The audit brief — the overlay's output artifact.

The brief records what was audited, which evasion hypotheses were tested
and their support status, and what seeds were handed off. It is a brief,
not an interrogation result: the interrogation engine's state artifact
stays canonical.

Stand-down rule, enforced in code: the brief must NEVER contain
collision, adjudication, refinement, or surprise sections. Those belong
to the interrogation engine. If the engine isn't running, the brief is
reported and the work stops.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from .ground import GroundMap
from .hypotheses import HypothesisRecord, H_OBFUSCATION

# Headings the overlay must never emit. A brief that collides or
# adjudicates has left its lane — the schema rejects it.
FORBIDDEN_SECTIONS = (
    "collision", "collide", "adjudicat", "refinement", "refine",
    "surprise",
)


class BriefError(ValueError):
    """Raised when a brief breaks the schema or the stand-down rule."""


def check_stand_down(rendered: str) -> None:
    """Reject rendered text that contains engine-owned sections."""
    headings = re.findall(r"^#{1,3}\s*(.+)$", rendered, re.MULTILINE)
    for heading in headings:
        lowered = heading.lower()
        for forbidden in FORBIDDEN_SECTIONS:
            if forbidden in lowered:
                raise BriefError(
                    f"Stand-down violation: the brief must not contain a "
                    f"'{heading.strip()}' section. Collision, adjudication, "
                    "refinement, and surprise belong to the interrogation "
                    "engine — this overlay audits and hands off, nothing more."
                )


@dataclass
class AuditBrief:
    """Audited ground + tested hypotheses + handoff seeds."""

    case_name: str
    ground: GroundMap = field(default_factory=GroundMap)
    records: list[HypothesisRecord] = field(default_factory=list)
    seeds: list[str] = field(default_factory=list)
    lifecycle: str = "FINAL"
    brief_date: str = field(default_factory=lambda: date.today().isoformat())

    def __post_init__(self) -> None:
        if not self.case_name.strip():
            raise BriefError("Brief needs a case name.")
        if self.lifecycle not in ("INITIAL", "ITERATIVE", "FINAL"):
            raise BriefError(f"Bad lifecycle: {self.lifecycle!r}.")
        if not (2 <= len(self.seeds) <= 3):
            raise BriefError(
                f"Handoff must produce 2-3 seed frames, got {len(self.seeds)}."
            )
        for seed in self.seeds:
            if not seed.strip():
                raise BriefError("Seed frames must not be empty.")

    def obfuscation_supported(self) -> bool:
        """True only when some record's H-obfuscation is supported."""
        return any(r.supports_obfuscation() for r in self.records)

    def render(self) -> str:
        lines = [
            "---",
            "artifact: audit-brief",
            f"date: {self.brief_date}",
            "protocol: fairit/1.0",
            f"lifecycle: {self.lifecycle}",
            "---",
            "",
            f"# Audit brief: {self.case_name}",
            "",
            self.ground.render(),
            "",
            "## Tested hypotheses",
        ]
        for record in self.records:
            lines.append("")
            lines.append(record.summary())
        lines.extend(["", "## Handoff seeds"])
        for i, seed in enumerate(self.seeds, 1):
            lines.append(f"{i}. {seed}")
        rendered = "\n".join(lines)
        check_stand_down(rendered)
        return rendered


def parse(rendered: str) -> AuditBrief:
    """Parse a rendered brief back into an AuditBrief.

    Round-trip fidelity: case name, lifecycle, date, and seeds survive.
    Ground and hypothesis records parse back as their raw text — the
    structured re-validation is the caller's job on re-entry.
    """
    check_stand_down(rendered)
    front = dict(
        line.split(":", 1)
        for line in rendered.splitlines()
        if re.match(r"^(artifact|date|protocol|lifecycle):", line)
    )
    if front.get("artifact", "").strip() != "audit-brief":
        raise BriefError("Not an audit-brief artifact.")
    match = re.search(r"^# Audit brief: (.+)$", rendered, re.MULTILINE)
    if not match:
        raise BriefError("Brief is missing its case-name heading.")
    seed_lines: list[str] = []
    if "## Handoff seeds" in rendered:
        tail = rendered.split("## Handoff seeds", 1)[1]
        seed_lines = [s.strip() for s in re.findall(r"^\d+\. (.+)$", tail, re.MULTILINE)]
    return AuditBrief(
        case_name=match.group(1).strip(),
        lifecycle=front.get("lifecycle", "FINAL").strip() or "FINAL",
        brief_date=front.get("date", "").strip() or date.today().isoformat(),
        seeds=seed_lines,
    )
