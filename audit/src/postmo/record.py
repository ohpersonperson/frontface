"""The audit record — the canonical artifact of a session.

Ryan's design call: the FULL structured record. Every discipline that
fired, every held tension, every person-state sequence, every typed
correction, every softening and motive flag — as structured data the
next session can load and continue from, with timestamps. Machine-
readable first, renderable conversationally (`render_conversation()`
produces the human surface the skill's output shape calls for).

Stand-down rule, enforced in code: the audit never resolves. The
record must not contain synthesis, resolution, or verdict sections —
a record that resolves has stopped auditing and started narrating.
`check_stand_down()` rejects both on render and on parse.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from .disciplines import DISCIPLINES, discipline_name
from .evidence import EvidenceItem
from .scans import (
    Correction, HeldTension, MotiveFlag, PersonState, SofteningFlag,
)

PROTOCOL = "postmo/1.0"

# Headings an audit record must never contain. An audit that synthesizes
# or resolves has left its lane — the schema rejects it.
# Stems chosen to actually match: "resolut" catches resolution/resolve/
# resolved ("resolv" would miss "resolution" — no v in r-e-s-o-l-u).
FORBIDDEN_SECTIONS = ("synthes", "resolut", "verdict", "conclus")


class RecordError(ValueError):
    """Raised when a record breaks the schema or the stand-down rule."""


def check_stand_down(rendered: str) -> None:
    """Reject rendered text with resolution/narration sections."""
    headings = re.findall(r"^#{1,3}\s*(.+)$", rendered, re.MULTILINE)
    for heading in headings:
        lowered = heading.lower()
        for forbidden in FORBIDDEN_SECTIONS:
            if forbidden in lowered:
                raise RecordError(
                    f"Stand-down violation: the audit record must not contain "
                    f"a '{heading.strip()}' section. The audit holds "
                    "contradictions — it never synthesizes, resolves, or "
                    "issues verdicts."
                )


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


@dataclass(frozen=True)
class DisciplineEntry:
    """One discipline enforcement, timestamped.

    action: "enforced" (the discipline shaped the session),
    "flagged" (a mechanical check fired — REVIEW item),
    "reviewed" (the operator judged a flagged item).
    """

    discipline: int
    action: str
    detail: str
    timestamp: str = field(default_factory=utc_now)

    def __post_init__(self) -> None:
        if self.discipline not in DISCIPLINES:
            raise RecordError(f"Unknown discipline: {self.discipline!r}.")
        if self.action not in ("enforced", "flagged", "reviewed"):
            raise RecordError(f"Bad discipline action: {self.action!r}.")
        if not self.detail.strip():
            raise RecordError("Discipline entry needs a detail.")


@dataclass
class AuditRecord:
    """The full structured record of an audit session."""

    case_name: str
    tensions: list[HeldTension] = field(default_factory=list)
    states: list[PersonState] = field(default_factory=list)
    corrections: list[Correction] = field(default_factory=list)
    motive_flags: list[MotiveFlag] = field(default_factory=list)
    softening_flags: list[SofteningFlag] = field(default_factory=list)
    discipline_log: list[DisciplineEntry] = field(default_factory=list)
    evidence: list[EvidenceItem] = field(default_factory=list)
    lifecycle: str = "FINAL"
    record_date: str = field(default_factory=lambda: date.today().isoformat())

    def __post_init__(self) -> None:
        if not self.case_name.strip():
            raise RecordError("Audit record needs a case name.")
        if self.lifecycle not in ("INITIAL", "ITERATIVE", "FINAL"):
            raise RecordError(f"Bad lifecycle: {self.lifecycle!r}.")

    # -- building helpers ----------------------------------------------------

    def log(self, discipline: int, action: str, detail: str) -> DisciplineEntry:
        """Append a timestamped discipline-log entry; returns it."""
        entry = DisciplineEntry(discipline=discipline, action=action, detail=detail)
        self.discipline_log.append(entry)
        return entry

    def core_claim_changes(self) -> list[Correction]:
        """The signal (D3): corrections that changed the account itself."""
        return [c for c in self.corrections if c.kind == "core-claim"]

    def states_for(self, person: str) -> list[PersonState]:
        """One person's time-indexed sequence (D2)."""
        return [s for s in self.states if s.person.lower() == person.lower()]

    # -- rendering -------------------------------------------------------------

    def render(self) -> str:
        """The machine-readable record: frontmatter + structured sections."""
        lines = [
            "---",
            "artifact: audit-record",
            f"date: {self.record_date}",
            f"protocol: {PROTOCOL}",
            f"lifecycle: {self.lifecycle}",
            "---",
            "",
            f"# Audit record: {self.case_name}",
            "",
            "## Held tensions (discipline 1)",
        ]
        for t in self.tensions:
            lines.append(f"- {t.text}")
        lines.append("")
        lines.append("## Person-state sequences (discipline 2)")
        for s in self.states:
            lines.append(f"- [{s.when}] {s.person}: {s.state}")
        lines.append("")
        lines.append("## Corrections (discipline 3)")
        for c in self.corrections:
            lines.append(f"- ({c.kind}) {c.text}")
        lines.append("")
        lines.append("## Motive flags (discipline 4)")
        for m in self.motive_flags:
            lines.append(f"- [{m.severity}] {m.sentence} — {m.pattern}")
        lines.append("")
        lines.append("## Softening flags (discipline 5)")
        for f in self.softening_flags:
            lines.append(f"- [{f.kind}] {f.detail}")
        lines.append("")
        lines.append("## Discipline log")
        for e in self.discipline_log:
            lines.append(
                f"- [{e.timestamp}] D{e.discipline} "
                f"({discipline_name(e.discipline)}) {e.action}: {e.detail}"
            )
        lines.append("")
        lines.append("## Evidence")
        for item in self.evidence:
            lines.append(f"- [{item.tag}] {item.text}")
        rendered = "\n".join(lines)
        check_stand_down(rendered)
        return rendered

    def render_conversation(self) -> str:
        """The human surface: the record's contents in conversational form.

        This is a digest, not a conversation — the operator's actual
        replies stay with the operator. It names held tensions explicitly
        ("Both of these are true, and I'm not picking one"), gives
        per-person accounts, names correction types before responding to
        them, and surfaces flags inline, per the skill's output shape.
        """
        parts = [f"Auditing: {self.case_name}", ""]
        if self.tensions:
            parts.append(
                "Both of these are true, and I'm not picking one:"
            )
            for t in self.tensions:
                parts.append(f"  {t.text}")
            parts.append("")
        people = sorted({s.person for s in self.states})
        for person in people:
            seq = self.states_for(person)
            states = "; ".join(f"{s.when}: {s.state}" for s in seq)
            parts.append(f"{person} — {states}.")
        if people:
            parts.append("")
        for c in self.corrections:
            parts.append(
                f"Correction typed as {c.kind}: {c.text}"
            )
        if self.corrections:
            parts.append("")
        for m in self.motive_flags:
            if m.severity == "flag":
                parts.append(
                    f"Flagging a supplied motive — the teller didn't state "
                    f"this why: {m.sentence}"
                )
            else:
                parts.append(
                    f"Marked as a guess (stays marked): {m.sentence}"
                )
        for f in self.softening_flags:
            parts.append(f"Softening check: {f.detail}")
        if self.motive_flags or self.softening_flags:
            parts.append("")
        parts.append(
            "Nothing here is resolved. The contradictions stay live; "
            "the sequences stay sequences."
        )
        rendered = "\n".join(parts)
        check_stand_down(rendered)
        return rendered


# --- parsing ------------------------------------------------------------------

_SECTION_RES = {
    "tensions": re.compile(r"^## Held tensions", re.MULTILINE),
    "states": re.compile(r"^## Person-state sequences", re.MULTILINE),
    "corrections": re.compile(r"^## Corrections", re.MULTILINE),
    "motive_flags": re.compile(r"^## Motive flags", re.MULTILINE),
    "softening_flags": re.compile(r"^## Softening flags", re.MULTILINE),
    "discipline_log": re.compile(r"^## Discipline log", re.MULTILINE),
    "evidence": re.compile(r"^## Evidence", re.MULTILINE),
}


def _section_text(rendered: str, key: str) -> str:
    match = _SECTION_RES[key].search(rendered)
    if not match:
        return ""
    tail = rendered[match.end():]
    next_heading = re.search(r"^## ", tail, re.MULTILINE)
    return tail[: next_heading.start()] if next_heading else tail


def parse(rendered: str) -> AuditRecord:
    """Parse a rendered record back into an AuditRecord.

    Round-trip fidelity: case name, lifecycle, date, and every
    structured section survive. Items re-validate on the way in —
    a hand-edited record with a subordinating tension or a bad tag
    fails here, not silently.
    """
    check_stand_down(rendered)
    front = dict(
        line.split(":", 1)
        for line in rendered.splitlines()
        if re.match(r"^(artifact|date|protocol|lifecycle):", line)
    )
    if front.get("artifact", "").strip() != "audit-record":
        raise RecordError("Not an audit-record artifact.")
    match = re.search(r"^# Audit record: (.+)$", rendered, re.MULTILINE)
    if not match:
        raise RecordError("Record is missing its case-name heading.")

    tensions = [
        HeldTension(text=line[2:].strip())
        for line in _section_text(rendered, "tensions").splitlines()
        if line.startswith("- ")
    ]
    states: list[PersonState] = []
    for line in _section_text(rendered, "states").splitlines():
        if line.startswith("- "):
            m = re.match(r"^- \[(.+?)\] (.+?): (.+)$", line)
            if not m:
                raise RecordError(f"Unparseable person-state line: {line!r}")
            states.append(PersonState(when=m.group(1), person=m.group(2),
                                      state=m.group(3)))
    corrections: list[Correction] = []
    for line in _section_text(rendered, "corrections").splitlines():
        if line.startswith("- "):
            m = re.match(r"^- \((detail|core-claim)\) (.+)$", line)
            if not m:
                raise RecordError(f"Unparseable correction line: {line!r}")
            corrections.append(Correction(kind=m.group(1), text=m.group(2)))
    motive_flags: list[MotiveFlag] = []
    for line in _section_text(rendered, "motive_flags").splitlines():
        if line.startswith("- "):
            m = re.match(r"^- \[(flag|guess)\] (.+?) — (.+)$", line)
            if not m:
                raise RecordError(f"Unparseable motive-flag line: {line!r}")
            motive_flags.append(MotiveFlag(sentence=m.group(2),
                                           pattern=m.group(3),
                                           severity=m.group(1)))
    softening_flags: list[SofteningFlag] = []
    for line in _section_text(rendered, "softening_flags").splitlines():
        if line.startswith("- "):
            m = re.match(
                r"^- \[(downgrade|dropped|tidy-restatement|ambivalence-resolved)\] (.+)$",
                line,
            )
            if not m:
                raise RecordError(f"Unparseable softening-flag line: {line!r}")
            softening_flags.append(SofteningFlag(kind=m.group(1), detail=m.group(2)))
    discipline_log: list[DisciplineEntry] = []
    for line in _section_text(rendered, "discipline_log").splitlines():
        if line.startswith("- "):
            m = re.match(
                r"^- \[(.+?)\] D(\d) \((.+?)\) (enforced|flagged|reviewed): (.+)$",
                line,
            )
            if not m:
                raise RecordError(f"Unparseable discipline-log line: {line!r}")
            discipline_log.append(DisciplineEntry(
                discipline=int(m.group(2)), action=m.group(4),
                detail=m.group(5), timestamp=m.group(1)))
    evidence: list[EvidenceItem] = []
    for line in _section_text(rendered, "evidence").splitlines():
        if line.startswith("- "):
            m = re.match(r"^- \[(.+?)\] (.+)$", line)
            if not m:
                raise RecordError(f"Unparseable evidence line: {line!r}")
            evidence.append(EvidenceItem(text=m.group(2), tag=m.group(1)))

    return AuditRecord(
        case_name=match.group(1).strip(),
        tensions=tensions,
        states=states,
        corrections=corrections,
        motive_flags=motive_flags,
        softening_flags=softening_flags,
        discipline_log=discipline_log,
        evidence=evidence,
        lifecycle=front.get("lifecycle", "FINAL").strip() or "FINAL",
        record_date=front.get("date", "").strip() or date.today().isoformat(),
    )
