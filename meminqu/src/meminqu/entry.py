"""Entry formatting: the inquiry-capture record.

The contract: answers are preserved verbatim — byte-identical. The
function adds structure around them (the inquiry marker, the register
list, question text) but never touches the answer text itself. If an
answer is empty (skipped question), the skip is recorded as a skip —
still capture, not silence.

Provenance vs fidelity: the ``SOURCE_TAG`` ("meminqu") stamped on the
capture says *where the entry entered the pipeline* (provenance). The
mandatory ``capture_mode`` recorded on every entry says *how it was
captured* (fidelity: VERBATIM / SUMMARY / PARAPHRASE). The two are
different claims, and the schema keeps them separate — a paraphrased
entry must never inherit the authority of a verbatim one.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from .registers import get_register


class CaptureMode(str, Enum):
    """How the operator captured the answers in one entry.

    VERBATIM  — written down exactly as answered.
    SUMMARY   — condensed by the operator; substance kept, words not.
    PARAPHRASE — restated in the operator's own words.
    """

    VERBATIM = "VERBATIM"
    SUMMARY = "SUMMARY"
    PARAPHRASE = "PARAPHRASE"


def normalize_capture_mode(value: CaptureMode | str | None) -> CaptureMode:
    """Validate a capture mode; omission or unknown values raise.

    Accepts a CaptureMode member or a string (case-insensitive).
    Never defaults silently: ``None`` and anything outside the three
    modes raise ValueError.
    """
    if value is None:
        raise ValueError(
            "capture_mode is required: VERBATIM, SUMMARY, or PARAPHRASE. "
            "Omission is a validation error — the mode must be stated, "
            "never defaulted."
        )
    if isinstance(value, CaptureMode):
        return value
    if isinstance(value, str):
        try:
            return CaptureMode[value.strip().upper()]
        except KeyError:
            pass
    raise ValueError(
        f"Invalid capture_mode {value!r}: must be one of "
        + ", ".join(m.value for m in CaptureMode)
    )


@dataclass(frozen=True)
class Response:
    """One question asked, and its answer (possibly skipped)."""

    register: str
    question: str
    answer: str | None = None


ENTRY_MARKER = "### Inquiry capture"


def format_entry(
    domain: str,
    responses: list[Response],
    *,
    capture_mode: CaptureMode | str | None = None,
) -> str:
    """Build the capture entry body for one domain.

    Raises ValueError on an empty response list, unknown register
    names, or a missing/invalid ``capture_mode``. Answers are embedded
    verbatim — this function performs no normalization, trimming, or
    interpretation on them. The mode is a fidelity claim about *how*
    the operator captured the answers; it is stored in the entry body
    and is separate from the meminqu SOURCE_TAG (provenance).
    """
    if not responses:
        raise ValueError("Cannot format an entry with no responses.")
    mode = normalize_capture_mode(capture_mode)
    registers_used: list[str] = []
    for resp in responses:
        reg = get_register(resp.register)
        if reg.name not in registers_used:
            registers_used.append(reg.name)

    lines = [
        f"{ENTRY_MARKER} — {domain} (registers: {', '.join(registers_used)})",
        f"capture_mode: {mode.value}",
        "",
    ]
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
