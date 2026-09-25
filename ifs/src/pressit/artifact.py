"""The state artifact: the portable, self-contained deliverable of an
interrogation.

One field, one canonical current state file, named
``interrogation-state-[field-slug].md``. Another person (or model) must be
able to continue the investigation from the artifact alone — never
"see above", never "as discussed", never unstated context, never memory.

Persistence boundary: the engine's responsibility ends when the complete
artifact has been emitted. The *caller* saves it to disk and supplies it to
future interrogations. The engine never writes files and never claims
external persistence occurred.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from .protocol import (
    KEY_CLASSIFICATIONS, CONFIDENCES, PRIOR_DISPOSITIONS,
    SESSION_LIFECYCLES, PROTOCOL_NAME, PROTOCOL_VERSION,
    required_collision_pairs, validate_keys, KeyDraft,
)

SCHEMA_SECTIONS = (
    "Interrogation Metadata", "Prior State", "1. Identify", "2. Decompose",
    "3. Diverge", "4. Collide", "5. Refine", "6. Surprise",
    "7. Synthesize", "State Status",
)


class ArtifactError(ValueError):
    """Raised when an artifact breaks the canonical schema."""


@dataclass
class PriorKeyEvaluation:
    statement: str
    status: str  # HELD | CRACKED | MODIFIED | SUPERSEDED | UNRESOLVED
    note: str

    def __post_init__(self) -> None:
        status = self.status.strip().upper()
        if status not in PRIOR_DISPOSITIONS:
            raise ArtifactError(f"Bad prior-Key disposition: {self.status!r}.")
        self.status = status


@dataclass
class Take:
    id: str
    title: str
    argument: str


@dataclass
class Collision:
    pair: str
    contradiction: str
    premise_failure: str
    discriminator: str


@dataclass
class Synthesis:
    established_ground: str
    surviving_model: str
    remaining_uncertainties: str
    primary_next_target: str


@dataclass
class StateArtifact:
    """A complete, validated interrogation state."""

    field: str
    session: int
    date: str  # YYYY-MM-DD
    depth: str  # one-pass | deep
    trigger_context: str
    lifecycle: str  # INITIAL | ITERATIVE | FINAL
    prior_interrogation: int | None
    prior_date: str | None
    prior_keys: list[PriorKeyEvaluation]
    takes: list[Take]
    collisions: list[Collision]
    keys: list[KeyDraft]
    surprise: str | None
    synthesis: Synthesis
    evidence_summary: str = ""
    interrogation: int = 1

    def __post_init__(self) -> None:
        if self.session < 1:
            raise ArtifactError("Session number must be >= 1.")
        if self.lifecycle not in SESSION_LIFECYCLES:
            raise ArtifactError(f"Bad lifecycle: {self.lifecycle!r}.")
        pairs = required_collision_pairs([t.id for t in self.takes])
        got = [c.pair for c in self.collisions]
        if got != pairs:
            raise ArtifactError(
                f"Collision pairs must be exactly {pairs}, got {got}."
            )
        validate_keys(self.keys)

    @property
    def slug(self) -> str:
        return slugify_field(self.field)

    @property
    def filename(self) -> str:
        return f"interrogation-state-{self.slug}.md"


def slugify_field(name: str) -> str:
    slug = name.lower()
    slug = re.sub(r"['\"]", "", slug)
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = slug.strip("-")[:64].strip("-")
    return slug or "field"


def render_frontmatter(a: StateArtifact) -> str:
    return (
        "---\n"
        "artifact: interrogation-state\n"
        f"field: {a.slug}\n"
        f"interrogation: {a.interrogation}\n"
        f"date: {a.date}\n"
        f"depth: {a.depth}\n"
        f"trigger_context: {a.trigger_context}\n"
        "status: complete\n"
        f"lifecycle: {a.lifecycle}\n"
        f"protocol: {PROTOCOL_NAME}/{PROTOCOL_VERSION}\n"
        "persistence: external\n"
        "canonical: true\n"
        "---"
    )


def render(a: StateArtifact) -> str:
    """Render the full canonical Markdown artifact."""
    a.__post_init__()  # re-validate before emission
    fm = render_frontmatter(a)

    prior_lines = [
        f"- Prior interrogation: {a.prior_interrogation if a.prior_interrogation else 'Not supplied'}",
        f"- Prior date: {a.prior_date or '—'}",
    ]
    if a.prior_keys:
        prior_lines.append("- Key dispositions:")
        for k in a.prior_keys:
            prior_lines.append(f"  - {k.status}: {k.statement} — {k.note}")
    else:
        prior_lines.append("- Key dispositions: none (session 1)")

    take_lines = []
    for t in a.takes:
        take_lines.append(f"### Take {t.id} — {t.title}\n\n{t.argument}")

    collision_lines = []
    for c in a.collisions:
        collision_lines.append(
            f"### Pair {c.pair}\n\n"
            f"- Contradiction: {c.contradiction}\n"
            f"- Premise that must break: {c.premise_failure}\n"
            f"- Discriminator: {c.discriminator}"
        )

    key_lines = []
    for i, k in enumerate(a.keys, 1):
        key_lines.append(
            f"### Key {i}\n\n"
            f"- Statement: {k.statement}\n"
            f"- Classification: {k.classification}\n"
            f"- Evidence: {k.evidence}\n"
            f"- Confidence: {k.confidence}\n"
            f"- Structural vulnerability: {k.vulnerability}\n"
            f"- Falsifier: {k.falsifier}"
        )

    body = "\n\n".join([
        fm,
        f"# Interrogation State: {a.field}",
        "## Interrogation Metadata\n"
        f"- Date: {a.date}\n"
        f"- Field: {a.field}\n"
        f"- Depth: {a.depth}\n"
        f"- Interrogation: {a.interrogation}\n"
        f"- Trigger context: {a.trigger_context}\n"
        f"- Protocol: {PROTOCOL_NAME}/{PROTOCOL_VERSION}\n"
        f"- Lifecycle: {a.lifecycle}",
        "## Prior State\n" + "\n".join(prior_lines),
        f"## 1. Identify\n- Field: {a.field}\n- Trigger: {a.trigger_context}",
        f"## 2. Decompose\n{a.evidence_summary or '(evidence logged with the interrogation)'}",
        "## 3. Diverge\n\n" + "\n\n".join(take_lines),
        "## 4. Collide\n\n" + "\n\n".join(collision_lines),
        "## 5. Refine\n\n" + "\n\n".join(key_lines),
        "## 6. Surprise\n\n" + (a.surprise or "No material Surprise identified."),
        "## 7. Synthesize\n"
        f"- Established: {a.synthesis.established_ground}\n"
        f"- Surviving model: {a.synthesis.surviving_model}\n"
        f"- Remaining uncertainties: {a.synthesis.remaining_uncertainties}\n"
        f"- Primary next target: {a.synthesis.primary_next_target}",
        "## State Status\n"
        f"- Interrogation: Complete\n"
        f"- Lifecycle: {a.lifecycle}\n"
        f"- State: Canonical\n"
        f"- Persistence: External\n"
        "- External save: performed by the caller, not the engine",
    ])
    return body + "\n"


def check_sections(markdown: str) -> list[str]:
    """Return any canonical schema sections missing from rendered Markdown."""
    return [s for s in SCHEMA_SECTIONS if f"## {s}" not in markdown]


@dataclass
class PriorState:
    """A loaded prior artifact for stress-testing in session 2+."""

    artifact: StateArtifact

    def dispositions(self) -> list[PriorKeyEvaluation]:
        return self.artifact.prior_keys

    def next_session(self) -> int:
        return self.artifact.interrogation + 1


def load_prior(markdown: str) -> dict:
    """Extract the prior Keys and session number from a saved artifact.

    Returns {'interrogation': int, 'keys': [statements...]}. The engine uses
    this to stress-test each prior Key and assign dispositions — it never
    inherits a prior conclusion as established.
    """
    keys: list[str] = []
    for m in re.finditer(r"- Statement:\s*(.+)", markdown):
        keys.append(m.group(1).strip())
    session = 1
    m = re.search(r"^interrogation:\s*(\d+)", markdown, re.M)
    if m:
        session = int(m.group(1))
    return {"interrogation": session, "keys": keys}
