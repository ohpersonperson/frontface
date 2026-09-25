"""The seven registers: deliberately different question stances.

This is the actual mechanism of the interview. Each register is a
distinct way of approaching the same domain — direct, reflective,
structural, irreverent, sparse, temporal, contrastive — so the answers
don't all come from the same angle. The registers are data: a caller
can supply their own set, but the shipped seven are the skill's
complete, unmodified set.
"""

from __future__ import annotations

from dataclasses import dataclass


class RegisterError(ValueError):
    """Raised for unknown register names or bad register sets."""


@dataclass(frozen=True)
class Register:
    """One question stance."""

    name: str
    label: str
    description: str
    example_stems: tuple[str, ...]


REGISTERS: tuple[Register, ...] = (
    Register(
        name="direct",
        label="Direct / forensic",
        description=(
            "No framing, no softening. Ask for the facts as they are, "
            "the way a deposition would."
        ),
        example_stems=(
            "State the single most important fact in this domain right now, with no qualifiers.",
            "What happened here that you would swear to under oath?",
        ),
    ),
    Register(
        name="reflective",
        label="Reflective / interior",
        description=(
            "How it feels from the inside. Subjective material the "
            "forensic register can't reach."
        ),
        example_stems=(
            "What does this domain feel like from the inside this week?",
            "What has been sitting in the back of your mind about it?",
        ),
    ),
    Register(
        name="structural",
        label="Structural / systems",
        description=(
            "The machinery underneath: routines, dependencies, "
            "load-bearing parts, failure points."
        ),
        example_stems=(
            "What system or routine governs this domain? Which parts are load-bearing?",
            "If this domain were a machine, which part is under the most strain?",
        ),
    ),
    Register(
        name="irreverent",
        label="Irreverent / cutting",
        description=(
            "Deliberately disrespectful of the domain's official story. "
            "Politeness is a filter; this register removes it."
        ),
        example_stems=(
            "Cut the diplomacy: what is actually going on here?",
            "What is the most embarrassing truth about this domain you would rather not admit?",
        ),
    ),
    Register(
        name="sparse",
        label="Sparse / minimal",
        description=(
            "Compression as a forcing function. What survives when "
            "there is almost no room says what matters."
        ),
        example_stems=(
            "This domain in one sentence.",
            "Three words. No more.",
        ),
    ),
    Register(
        name="temporal",
        label="Temporal / what's alive now",
        description=(
            "Time-indexed. What is true *now*, what changed, what is "
            "moving — not the domain's permanent self-image."
        ),
        example_stems=(
            "What is alive in this domain right now, today?",
            "What changed here since the last time you looked at it?",
        ),
    ),
    Register(
        name="contrastive",
        label="Contrastive / what is not true",
        description=(
            "Approach by negation. False appearances and near-misses "
            "define the edges of what is real here."
        ),
        example_stems=(
            "What is *not* true about this domain, though it might look that way?",
            "What would surprise someone who only saw the surface?",
        ),
    ),
)

_REGISTER_INDEX = {r.name: r for r in REGISTERS}


def get_register(name: str) -> Register:
    """Return the register with this name, or raise RegisterError."""
    key = name.strip().lower()
    if key not in _REGISTER_INDEX:
        raise RegisterError(
            f"Unknown register {name!r}. Known registers: "
            f"{', '.join(r.name for r in REGISTERS)}."
        )
    return _REGISTER_INDEX[key]


def validate_register_set(registers: tuple[Register, ...]) -> tuple[Register, ...]:
    """Check a caller-supplied register set: unique names, usable stems."""
    if len(registers) < 2:
        raise RegisterError("A register set needs at least two registers.")
    seen: set[str] = set()
    for r in registers:
        key = r.name.strip().lower()
        if not key:
            raise RegisterError("Register names must not be blank.")
        if key in seen:
            raise RegisterError(f"Duplicate register: {r.name!r}.")
        seen.add(key)
        if not r.example_stems:
            raise RegisterError(f"Register {r.name!r} has no example stems.")
    return registers


def plan_cycle(
    domains: tuple[str, ...] | list[str],
    per_domain: int = 3,
    registers: tuple[Register, ...] = REGISTERS,
) -> dict[str, list[str]]:
    """Assign registers to each domain for one interview cycle.

    Rotation rule: consecutive domains never share the same register
    set, and the offset advances each domain so every register gets
    used across a full cycle. Deterministic — the same inputs always
    produce the same plan.
    """
    registers = validate_register_set(tuple(registers))
    domains = tuple(domains)
    if not domains:
        raise RegisterError("Need at least one domain to plan a cycle.")
    if per_domain < 1:
        raise RegisterError("per_domain must be at least 1.")
    if per_domain > len(registers):
        raise RegisterError(
            f"per_domain ({per_domain}) exceeds the register count "
            f"({len(registers)})."
        )
    names = [r.name for r in registers]
    n = len(names)
    plan: dict[str, list[str]] = {}
    for i, domain in enumerate(domains):
        start = (i * per_domain) % n
        plan[domain] = [names[(start + j) % n] for j in range(per_domain)]
    return plan
