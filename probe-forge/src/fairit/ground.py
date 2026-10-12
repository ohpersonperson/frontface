"""Ground mapping — the pre-interrogation audit of situational state.

Objective: establish exactly what is the case WITHOUT forcing narrative
resolution. Three outputs:

- Held tensions: opposing facts stated as parallel, non-subordinating
  sentences ("X is true. Y is also true."). Never "X, but Y" — the
  subordinating conjunction quietly privileges one side, which is a
  resolution smuggled in as grammar.
- Time-indexed person-state sequence: people change across time; map the
  states, never flatten a person to one characterization.
- Corrections typed as detail vs core-claim: fixing a date is a detail;
  changing what was claimed to have happened is a core-claim change —
  and the latter is the signal.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime, timezone

# Subordinating conjunctions that privilege one side of a tension.
# "X is true. Y is also true." stays. "X is true, but Y" is rejected —
# the "but" resolves the contradiction by demoting X.
SUBORDINATORS = (
    "but", "however", "although", "though", "yet", "whereas",
    "nevertheless", "nonetheless", "which means", "in other words",
    "so really", "that is to say",
)

_SUB_RE = re.compile(
    r"\b(" + "|".join(re.escape(s) for s in SUBORDINATORS) + r")\b",
    re.IGNORECASE,
)


class GroundError(ValueError):
    """Raised when mapped ground breaks the audit rules."""


def find_subordinators(text: str) -> list[str]:
    """Return the subordinating conjunctions found in the text."""
    return sorted({m.group(0).lower() for m in _SUB_RE.finditer(text)})


# PARAM-FAIRIT-003 (Suite 2 / S2-03): the vacuity line for `PersonState.when`.
#
# Judgment call (documented, minimal): a time-index is rejected only when
# it asserts NO time information at all — exact match (after strip/lower/
# whitespace-collapse) against this small denylist. "sometime in June"
# still indexes June and stays the operator's content; the check guards
# structure (a vacuous time-index), not content (how the operator phrases
# time). Per the adjudication, this is not a date-parser commitment, so
# everything outside the denylist passes construction.
VACUOUS_WHENS = frozenset({
    "sometime", "some time", "someday", "eventually", "whenever",
    "unknown", "n/a", "tbd", "?",
})


def _normalize_when(value: str) -> str:
    return " ".join(value.strip().lower().split())


def is_vacuous_when(value: str) -> bool:
    """True when a `when` value names no time at all (PARAM-FAIRIT-003)."""
    return _normalize_when(value) in VACUOUS_WHENS


def when_sort_key(value: str) -> datetime | None:
    """A sortable key for a `when` value, or None when unparseable.

    Only ISO-8601 dates/datetimes participate in sequence ordering —
    deliberately not a full date parser (adjudicated scope: lightweight
    parseability, not a date-parser commitment). Unparseable values
    ("during the standup", "last Tuesday") pass through unchecked; the
    ordering check runs only over the values it can compare.
    """
    parts = _when_parts(value)
    return parts[0] if parts is not None else None


# A time component in an ISO-8601 value: "T09:00" or " 09:00:00".
_TIME_RE = re.compile(r"[T ]\d{2}:\d{2}")


def _when_parts(value: str) -> tuple[datetime, bool] | None:
    """(canonical key, has_time) for a when-value, or None when unparseable.

    has_time is False for date-only values ("2026-09-20"): a bare date
    asserts day-granularity, not midnight — so a same-day date/datetime
    mix (["2026-08-15T09:00", "2026-08-15"]) is not misread as out of
    order. Review E1 (Willow): treating date-only as midnight produced a
    false GroundError on legitimate same-day input.
    """
    text = value.strip()
    try:
        dt = datetime.fromisoformat(text)
    except ValueError:
        return None
    if dt.tzinfo is not None:
        # Aware datetimes normalize to UTC-naive; naive values are taken
        # as UTC. Mixing local-naive with offset forms can misorder —
        # inherent to a lightweight check with no timezone policy, so the
        # assumption is stated here rather than hidden. Review E3 (Willow).
        dt = dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt, bool(_TIME_RE.search(text))


def _when_precedes(newer: tuple[datetime, bool],
                   older: tuple[datetime, bool]) -> bool:
    """True when time-index `newer` is strictly before `older`.

    Day-granularity grace: if either side is date-only, compare dates —
    a bare date means "that day", so ["2026-08-15T09:00", "2026-08-15"]
    is same-day, not backward.
    """
    (k_new, t_new), (k_old, t_old) = newer, older
    if t_new and t_old:
        return k_new < k_old
    return k_new.date() < k_old.date()


def _when_equal(a: str, b: str) -> bool:
    """True when two when-values denote the same time-index.

    Parseable values compare canonically — so a correction citing
    "2026-09-20T00:00:00" matches a state indexed "2026-09-20" (review
    E2: both reviewers — string-equality rejected the same instant
    spelled differently). When either side is date-only the comparison
    runs at day granularity. Anything unparseable falls back to
    normalized-string comparison, the same form the vacuity check uses.
    """
    pa, pb = _when_parts(a), _when_parts(b)
    if pa is None or pb is None:
        return _normalize_when(a) == _normalize_when(b)
    (ka, ta), (kb, tb) = pa, pb
    if ta and tb:
        return ka == kb
    return ka.date() == kb.date()


@dataclass(frozen=True)
class HeldTension:
    """One pair of opposing facts, held live as parallel sentences."""

    text: str

    def __post_init__(self) -> None:
        if not self.text.strip():
            raise GroundError("Held tension must not be empty.")
        bad = find_subordinators(self.text)
        if bad:
            raise GroundError(
                f"Held tension uses subordinating language {bad}: "
                f"{self.text!r}. Restate as parallel non-subordinating "
                "sentences — 'X is true. Y is also true.'"
            )


@dataclass(frozen=True)
class PersonState:
    """One person, one moment, one observed state. Time-indexed."""

    when: str
    person: str
    state: str

    def __post_init__(self) -> None:
        for label, value in (("when", self.when), ("person", self.person),
                             ("state", self.state)):
            if not value.strip():
                raise GroundError(f"PersonState.{label} must not be empty.")
        # PARAM-FAIRIT-003: a vacuous time-index ("sometime") is not a
        # time-index. Reject it at construction, like the other audit
        # rules — so the timeline can never silently carry one.
        if is_vacuous_when(self.when):
            raise GroundError(
                f"PersonState.when is vacuous {self.when!r}: a time-index "
                "must name a time, not the absence of one."
            )


@dataclass(frozen=True)
class Correction:
    """A correction typed by what changed.

    DETAIL: the facts stay the same, a detail was fixed (dates, names,
    sequence order). CORE-CLAIM: what was claimed to have happened
    changed. Core-claim changes are the signal — they mark where the
    account itself shifted.
    """

    kind: str  # "detail" | "core-claim"
    text: str
    # PARAM-FAIRIT-003: optional structured references to the ground the
    # correction touches. The audit used to validate only `kind` and
    # nonempty text, so a correction could cite a person/state that exists
    # nowhere in the map and nothing would notice. When these are given,
    # GroundMap checks them against the mapped states; when absent, no
    # check runs (no NLP over free text — references must be stated
    # structurally, not mined from prose). Both default empty, so existing
    # Correction(kind, text) constructions are unchanged.
    person: str = ""
    when: str = ""

    def __post_init__(self) -> None:
        if self.kind not in ("detail", "core-claim"):
            raise GroundError(
                f"Correction kind must be 'detail' or 'core-claim', got {self.kind!r}."
            )
        if not self.text.strip():
            raise GroundError("Correction text must not be empty.")


@dataclass
class GroundMap:
    """The audited ground: tensions held, states sequenced, corrections typed."""

    tensions: list[HeldTension] = field(default_factory=list)
    person_states: list[PersonState] = field(default_factory=list)
    corrections: list[Correction] = field(default_factory=list)

    def __post_init__(self) -> None:
        # PARAM-FAIRIT-003: the timeline is whole-sequence data, so the
        # checks run here, at construction, over the complete sequence —
        # not per-item. (GroundMap is mutable; post-hoc appends bypass
        # these checks, consistent with the rest of the package.)
        self._check_state_ordering()
        self._check_correction_references()

    def _check_state_ordering(self) -> None:
        """Each person's parseable `when` values must be non-decreasing.

        Judgment calls: ordering is per person (the timeline is a
        per-person sequence, so A's states need not sort against B's);
        equal values are allowed (two observations, one day); values the
        lightweight parser can't read neither order nor break the chain —
        they pass through as unknown points, not as violations. A bare
        date means "that day", not "midnight": same-day date/datetime
        mixes compare at day granularity (review E1).
        """
        last_seen: dict[str, tuple[datetime, bool]] = {}
        for state in self.person_states:
            parts = _when_parts(state.when)
            if parts is None:
                continue
            person = state.person.strip().casefold()
            previous = last_seen.get(person)
            if previous is not None and _when_precedes(parts, previous):
                raise GroundError(
                    f"PersonState sequence for {state.person!r} is out of "
                    f"order: {state.when!r} follows an earlier entry with a "
                    "later time-index. The timeline sequence must run "
                    "chronologically."
                )
            last_seen[person] = parts

    def _check_correction_references(self) -> None:
        """Corrections that name a person/when must resolve to mapped ground.

        Judgment call: references are optional — a correction with no
        `person`/`when` passes (the operator may not have a reference to
        state). But a reference that IS stated must be checkable: an
        unknown person, or a `when` with no matching state, is a dangling
        correction, and the audit fails loudly instead of carrying it
        silently. Name comparison is case-insensitive; `when` matches on
        the same normalized form the vacuity check uses.
        """
        for correction in self.corrections:
            person = correction.person.strip()
            when = correction.when.strip()
            if not person and not when:
                continue
            states = self.person_states
            if person:
                known = {
                    s.person.strip().casefold() for s in states
                }
                if person.casefold() not in known:
                    raise GroundError(
                        f"Correction ({correction.kind}) references unknown "
                        f"person {person!r}: no mapped PersonState for them. "
                        "A correction must reference checkable ground."
                    )
                states = [
                    s for s in states
                    if s.person.strip().casefold() == person.casefold()
                ]
            if when:
                # Semantic match, not string match: a correction citing
                # "2026-09-20T00:00:00" resolves against a state indexed
                # "2026-09-20" (review E2). Unparseable values fall back
                # to normalized-string comparison inside _when_equal.
                if not any(_when_equal(when, s.when) for s in states):
                    scope = f" for {person!r}" if person else ""
                    raise GroundError(
                        f"Correction ({correction.kind}) references unknown "
                        f"time-index {when!r}{scope}: no mapped PersonState "
                        "carries it. A correction must reference checkable "
                        "ground."
                    )

    def core_claim_changes(self) -> list[Correction]:
        """The signal: corrections that changed the account itself."""
        return [c for c in self.corrections if c.kind == "core-claim"]

    def render(self) -> str:
        lines = ["## Audited ground"]
        for t in self.tensions:
            lines.append(f"- Held tension: {t.text}")
        for p in self.person_states:
            lines.append(f"- State [{p.when}] {p.person}: {p.state}")
        for c in self.corrections:
            lines.append(f"- Correction ({c.kind}): {c.text}")
        if not (self.tensions or self.person_states or self.corrections):
            lines.append("- (no ground mapped)")
        return "\n".join(lines)
