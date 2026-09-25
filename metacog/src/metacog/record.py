"""Collision record: the canonical output of a pressure-test run.

Every run produces one compact, portable record — the trigger thresholds
that tripped, the countermodel, the assumption→collision map, the
confidence delta, any demotions, and the surprise check. Validation
enforces the protocol's hard rules: thresholds must have fired, only
load-bearing assumptions may be collided, revision follows collision,
and there are no placeholders.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

from .protocol import (
    COLLISION_RESULTS,
    LOAD_BEARING,
    CollisionResult,
    Countermodel,
    PROTOCOL_NAME,
    PROTOCOL_VERSION,
)
from .triggers import TriggerEvaluation

PLACEHOLDER_PATTERNS = (
    r"\[.*?\]",
    r"TODO",
    r"TBD",
    r"\.\.\.",
)


class RecordError(ValueError):
    """The collision record violates the protocol."""


def _no_placeholders(text: str, where: str) -> None:
    for pattern in PLACEHOLDER_PATTERNS:
        if re.search(pattern, text):
            raise RecordError(f"Placeholder text found in {where}: {pattern!r}")


@dataclass
class CollisionRecord:
    triggers: TriggerEvaluation
    countermodel: Countermodel
    assumptions: list = field(default_factory=list)  # list[Assumption]
    collisions: list = field(default_factory=list)  # list[CollisionResult]
    confidence_before: int = 0
    confidence_after: int = 0
    demotions: list[str] = field(default_factory=list)
    surprise: str = ""
    record_date: str = ""
    lifecycle: str = "INITIAL"

    def __post_init__(self) -> None:
        self.record_date = self.record_date or date.today().isoformat()

    def validate(self) -> None:
        # 1. Thresholds must have fired — a record from a stand-down is noise.
        if not self.triggers.fires:
            raise RecordError("Cannot record a run when no trigger threshold tripped.")
        # 2. Only load-bearing assumptions may be collided.
        load_bearing = {a.text for a in self.assumptions if a.load_bearing}
        for c in self.collisions:
            if c.assumption not in load_bearing:
                raise RecordError(
                    f"Collision targets non-load-bearing assumption: {c.assumption!r}. "
                    "Only load-bearing assumptions change conclusions."
                )
        # 3. Revision requires at least one collision — no evaluate-before-collide.
        if not self.collisions:
            raise RecordError(
                "Confidence revision with no collisions is self-report, not a finding."
            )
        # 4. Confidence values are 0-100.
        for name, value in (
            ("confidence_before", self.confidence_before),
            ("confidence_after", self.confidence_after),
        ):
            if not 0 <= value <= 100:
                raise RecordError(f"{name} must be 0-100, got {value!r}")
        # 5. No placeholders anywhere user-facing.
        _no_placeholders(self.countermodel.text, "countermodel")
        _no_placeholders(self.surprise, "surprise")
        for c in self.collisions:
            _no_placeholders(c.attack, "collision attack")

    def render(self) -> str:
        self.validate()
        lines = [
            "---",
            "artifact: collision-record",
            f"date: {self.record_date}",
            f"protocol: {PROTOCOL_NAME}/{PROTOCOL_VERSION}",
            f"lifecycle: {self.lifecycle}",
            "---",
            "",
            "# Collision Record",
            "",
            f"Trigger thresholds tripped: {', '.join(self.triggers.tripped)}",
            "",
            "## Countermodel",
            "",
            f"Strength: {self.countermodel.strength}",
            "",
            self.countermodel.text,
            "",
            "## Load-Bearing Assumptions",
            "",
        ]
        by_assumption = {c.assumption: c for c in self.collisions}
        for a in self.assumptions:
            lines.append(f"- [{a.kind}] {a.text}")
            if a.text in by_assumption:
                c = by_assumption[a.text]
                lines.append(f"  - collision: {c.result}")
                lines.append(f"  - attack: {c.attack}")
        lines += [
            "",
            "## Confidence",
            "",
            f"Before: {self.confidence_before} → After: {self.confidence_after} "
            f"(delta {self.confidence_after - self.confidence_before:+d})",
            "",
        ]
        if self.demotions:
            lines += ["## Demotions", ""]
            lines += [f"- {d}" for d in self.demotions]
            lines.append("")
        lines += ["## Surprise", "", self.surprise or "none recorded", ""]
        return "\n".join(lines)

    @classmethod
    def parse(cls, text: str) -> "CollisionRecord":
        """Parse a rendered record back. Raises RecordError on bad input."""
        fm: dict[str, str] = {}
        body = text
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) < 3:
                raise RecordError("Malformed frontmatter.")
            for line in parts[1].strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    fm[k.strip()] = v.strip()
            body = parts[2]
        if fm.get("artifact") != "collision-record":
            raise RecordError("Not a collision record.")
        # Minimal structural parse: triggers, countermodel, confidence.
        m_trig = re.search(r"Trigger thresholds tripped:\s*(.+)", body)
        tripped = [t.strip() for t in m_trig.group(1).split(",")] if m_trig else []
        m_conf = re.search(r"Before:\s*(\d+)\s*→\s*After:\s*(\d+)", body)
        before, after = (int(m_conf.group(1)), int(m_conf.group(2))) if m_conf else (0, 0)
        m_cm = re.search(r"## Countermodel\n\nStrength:\s*(\S+)\n\n(.+?)\n\n##", body, re.S)
        cm_text = m_cm.group(2).strip() if m_cm else ""
        cm_strength = m_cm.group(1).strip() if m_cm else "strong"
        m_sur = re.search(r"## Surprise\n\n(.+?)\s*$", body, re.S)
        surprise = m_sur.group(1).strip() if m_sur else ""
        return cls(
            triggers=TriggerEvaluation(tripped=tripped),
            countermodel=Countermodel(text=cm_text or "parsed", strength=cm_strength),
            confidence_before=before,
            confidence_after=after,
            surprise=surprise,
            record_date=fm.get("date", ""),
            lifecycle=fm.get("lifecycle", "INITIAL"),
        )
