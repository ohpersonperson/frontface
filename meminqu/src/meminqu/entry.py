"""Entry formatting: the inquiry-capture record.

The contract: answers are preserved verbatim — byte-identical. The
function adds structure around them (the inquiry marker, the register
list, question text) but never touches the answer text itself. If an
answer is empty (skipped question), the skip is recorded as a skip —
still capture, not silence.
"""

from __future__ import annotations

from dataclasses import dataclass

from .registers import get_register


@dataclass(frozen=True)
class Response:
    """One question asked, and its answer (possibly skipped)."""

    register: str
    question: str
    answer: str | None = None


ENTRY_MARKER = "### Inquiry capture"


def format_entry(domain: str, responses: list[Response]) -> str:
    """Build the capture entry body for one domain.

    Raises ValueError on an empty response list or unknown register
    names. Answers are embedded verbatim — this function performs no
    normalization, trimming, or interpretation on them.
    """
    if not responses:
        raise ValueError("Cannot format an entry with no responses.")
    registers_used: list[str] = []
    for resp in responses:
        reg = get_register(resp.register)
        if reg.name not in registers_used:
            registers_used.append(reg.name)

    lines = [f"{ENTRY_MARKER} — {domain} (registers: {', '.join(registers_used)})", ""]
    for resp in responses:
        reg = get_register(resp.register)
        lines.append(f"**[{reg.label}]** {resp.question.strip()}")
        if resp.answer is None or not resp.answer.strip():
            lines.append("_[no answer]_")
        else:
            # Verbatim: the answer text is appended exactly as given.
            lines.append(resp.answer)
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def answers_preserved_verbatim(body: str, responses: list[Response]) -> bool:
    """Check that every non-empty answer appears byte-identical in the body."""
    for resp in responses:
        if resp.answer and resp.answer.strip():
            if resp.answer not in body:
                return False
    return True
