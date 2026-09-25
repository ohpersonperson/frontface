"""Checkpoints and resume tokens: honest "not done yet" state.

A checkpoint is emitted only on a genuine limit — a context/length limit,
a session or tool interruption, or a low-confidence blocker with no safe
default. Never on fatigue, never on "this section feels done," never as a
soft way to stop early.

The resume token is a short, copy-pasteable pointer, not a cryptographic
token: `finish:<slug>-m<N>` (package:slug-milestoneIndex). Quoting it on
resume must let the session reconstruct where things stood from the
checkpoint block alone.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

TOKEN_RE = re.compile(r"^finish:([a-z0-9][a-z0-9-]*)-m(\d+)$")


class CheckpointError(ValueError):
    """A malformed checkpoint or resume token."""


def make_resume_token(slug: str, milestone_index: int) -> str:
    """Build a resume token like `finish:debate-sim-m3`."""
    slug = slug.strip().lower().replace(" ", "-")
    if not slug or milestone_index < 0:
        raise CheckpointError("Resume token needs a slug and a non-negative index.")
    return f"finish:{slug}-m{milestone_index}"


def parse_resume_token(token: str) -> tuple[str, int]:
    """Split a resume token into (slug, milestone_index). Validates format."""
    m = TOKEN_RE.match(token.strip())
    if not m:
        raise CheckpointError(
            f"Malformed resume token: {token!r}. Expected finish:<slug>-m<N>."
        )
    return m.group(1), int(m.group(2))


@dataclass
class Checkpoint:
    objective: str
    done: list[str] = field(default_factory=list)
    current: str = ""
    remaining: list[str] = field(default_factory=list)
    next_action: str = ""
    resume_token: str = ""
    blockers: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.objective.strip():
            raise CheckpointError("A checkpoint needs the locked objective.")
        if not self.resume_token.strip():
            raise CheckpointError("A checkpoint needs a resume token.")
        parse_resume_token(self.resume_token)  # validate format now

    def render(self) -> str:
        lines = [
            "FLASHY CHECKPOINT",
            f"OBJECTIVE  -> {self.objective}",
            f"DONE       -> {', '.join(self.done) if self.done else '(none yet)'}",
            f"CURRENT    -> {self.current or '(not started)'}",
            f"REMAINING  -> {', '.join(self.remaining) if self.remaining else '(none)'}",
            f"NEXT       -> {self.next_action or '(none recorded)'}",
            f"RESUME     -> {self.resume_token}",
        ]
        if self.blockers:
            lines.append(f"BLOCKERS   -> {', '.join(self.blockers)}")
        lines.append("")
        lines.append("Continuing...")
        return "\n".join(lines)

    @classmethod
    def parse(cls, text: str) -> "Checkpoint":
        """Parse a rendered checkpoint back. Raises CheckpointError on bad input."""
        if "FLASHY CHECKPOINT" not in text:
            raise CheckpointError("Not a Flashy checkpoint.")
        fields: dict[str, str] = {}
        for line in text.splitlines():
            if "->" in line:
                key, _, value = line.partition("->")
                fields[key.strip()] = value.strip()

        def split_list(value: str) -> list[str]:
            value = value.strip()
            if not value or value in ("(none yet)", "(none)"):
                return []
            return [p.strip() for p in value.split(",") if p.strip()]

        try:
            return cls(
                objective=fields["OBJECTIVE"],
                done=split_list(fields.get("DONE", "")),
                current="" if fields.get("CURRENT") == "(not started)" else fields.get("CURRENT", ""),
                remaining=split_list(fields.get("REMAINING", "")),
                next_action="" if fields.get("NEXT") == "(none recorded)" else fields.get("NEXT", ""),
                resume_token=fields["RESUME"],
                blockers=split_list(fields.get("BLOCKERS", "")),
            )
        except KeyError as exc:
            raise CheckpointError(f"Checkpoint missing field: {exc}") from exc
