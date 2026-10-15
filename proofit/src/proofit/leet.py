"""The 1337 module: Ryan's original four checks, as proofit rules R11-R14.

Origin: the four checks were the original asks of proofit — cross-role
duplication detection, header date check, suspicious-character-count
namesake, and missing-file verification. They first shipped as the
post-merge brief sanity gate in staff/langchain/leet.py (PARAM-1337,
2026-10-09), built after the morning standup's merged brief came out at
exactly 1,337 characters — header dated 2023-10-05, claiming MEMORY.md
was missing (it exists), with builder and verifier making the identical
false claim. On Ryan's 2026-10-12 clarification ("proofit"), the four
checks live here as first-class lint rules, wired into the proofit lint
run alongside R1-R10. The staff brief gate is untouched.

These rules are text-level, not runbook-shape checks: they read rb.raw
(header text, character count, role sections, file-existence claims)
rather than the parsed template structure. On a well-formed runbook
with no role sections, no header date, and no missing-file claims, they
fire nothing — narrow tripwires, fail-closed, same doctrine as R1-R10.
"""
from __future__ import annotations

import os
import re
from datetime import date

from .model import Runbook, Violation

# The namesake canon: the eight "cute lengths" from Ryan's order.
# Readings are his words (see staff/DEVLOG.md 2026-10-09 "1337 module:
# five more cute lengths" and the 93 / 222 / 1001 follow-ups).
CUTE_LENGTHS = {
    93: "93 93/93 — Crowley's current, as a dragonflies",
    222: "222 — Ryan's number (sometimes lucky)",
    555: "angel number (change); Thai hahaha",
    840: "twice as high (2 × 420)",
    1001: "1001 Arabian Nights — 10:01, reads the same in the mirror (I O O I)",
    1111: "angel number (make a wish)",
    1217: "1217 Chestnut St, Bowling Green — the old house",
    1337: "leet",
}

_HEADER_LINES = 12   # how far down the page the header date may live
_CLAIM_WINDOW = 80   # chars around a filename that must carry a "missing"-family word

# YYYY-MM-DD, 2000-2099 only — same narrow shape as the staff gate.
_DATE_RE = re.compile(r"\b(20\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])\b")
_FILENAME_RE = re.compile(r"(\S+\.(?:md|py|json|yaml|yml|txt|sh))", re.I)
_MISSING_WORD_RE = re.compile(
    r"missing|not found|doesn'?t exist|couldn'?t (?:be )?found|unable to (?:find|locate)",
    re.I,
)
# Role section headers: "### scout", "**Builder**", "SCOUT:" and the like.
_ROLE_HEADER_RE = re.compile(
    r"^\s*(?:#{1,6}\s+|\*{1,2})?\s*(scout|builder|verifier|clerk|runner)"
    r"\s*(?:\*{1,2}|:)?\s*$",
    re.I,
)

# Filesystem roots a bare claimed filename is checked against. Home first:
# brief-style claims like "MEMORY.md is missing" name files that live at ~.
_FILE_ROOTS = [
    os.path.expanduser("~"),
    os.getcwd(),
]


def _split_role_sections(text: str) -> list[tuple[str, str]]:
    """Split text into (role, section_text) pairs.

    Lines that name a role alone start a new section. Everything before
    the first role header is ("header", ...).
    """
    sections: list[tuple[str, str]] = []
    cur_role, cur_lines = "header", []
    for line in text.splitlines():
        m = _ROLE_HEADER_RE.match(line)
        if m:
            if cur_lines:
                sections.append((cur_role, "\n".join(cur_lines)))
            cur_role, cur_lines = m.group(1).lower(), []
        else:
            cur_lines.append(line)
    if cur_lines:
        sections.append((cur_role, "\n".join(cur_lines)))
    return sections


def _resolve_claim_path(claimed: str) -> str:
    """Resolve a claimed filename the way the staff gate does: ~/ first."""
    p = claimed.strip().strip("\"'(),.:;")
    if p.startswith("~/"):
        return os.path.join(os.path.expanduser("~"), p[2:])
    if p.startswith("/"):
        return p
    return os.path.join(_FILE_ROOTS[0], p)


def _missing_file_claims(text: str) -> list[tuple[str, str, bool]]:
    """Filenames asserted missing: (claimed_name, resolved_path, exists).

    The "missing"-family word must appear within _CLAIM_WINDOW chars of
    the filename — looser than a strict `X is missing` pattern on purpose,
    because brief prose says things like "MEMORY.md file is missing".
    """
    out: list[tuple[str, str, bool]] = []
    seen: set[str] = set()
    for m in _FILENAME_RE.finditer(text):
        claimed = m.group(1).strip("\"'(),.:;")
        key = claimed.lower()
        if key in seen:
            continue
        start = max(0, m.start() - _CLAIM_WINDOW)
        window = text[start:m.end() + _CLAIM_WINDOW]
        if _MISSING_WORD_RE.search(window):
            seen.add(key)
            path = _resolve_claim_path(claimed)
            out.append((claimed, path, os.path.exists(path)))
    return out


# ---------------------------------------------------------------------------
# R11 — Cross-role duplication detection (ERROR, fail-closed)
# ---------------------------------------------------------------------------
# Two or more roles making the same factual claim (the identical missing
# file, the identical off date) means poisoned shared context. Real
# independent observation rarely produces identical claims.
def check_r11_cross_role_dup(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    text = rb.raw or ""
    claim_roles: dict[str, set[str]] = {}
    for role, section in _split_role_sections(text):
        if role == "header":
            continue
        for claimed, _path, _exists in _missing_file_claims(section):
            claim_roles.setdefault("missing:" + claimed.lower(), set()).add(role)
        for m in _DATE_RE.finditer(section):
            claim_roles.setdefault("date:" + m.group(0), set()).add(role)
    today = date.today()
    for key in sorted(claim_roles):
        roles = claim_roles[key]
        if len(roles) < 2:
            continue
        kind, val = key.split(":", 1)
        role_list = ", ".join(sorted(roles))
        if kind == "date":
            # Every role dating its own section today is normal; two roles
            # agreeing on an OFF date is shared-context poison.
            try:
                d = date(*map(int, val.split("-")))
            except ValueError:
                out.append(Violation(
                    rule=11,
                    location="document",
                    message=f"cross-role duplication: invalid date '{val}' "
                            f"repeated by {role_list}",
                    fix="agree on one true date — an invalid date repeated "
                        "across roles is poisoned shared context",
                ))
                continue
            if abs((today - d).days) > 1:
                out.append(Violation(
                    rule=11,
                    location="document",
                    message=f"cross-role duplication: off date '{val}' "
                            f"repeated by {role_list}",
                    fix="date each role's section today; a shared off date "
                        "is poisoned shared context",
                ))
        else:
            out.append(Violation(
                rule=11,
                location="document",
                message=f"cross-role duplication: '{val}' claimed missing by "
                        f"{role_list} — independent roles rarely make "
                        "identical factual claims",
                fix="verify the claim against the filesystem before repeating it",
            ))
    return out


# ---------------------------------------------------------------------------
# R12 — Header date check (ERROR, fail-closed)
# ---------------------------------------------------------------------------
# A document dated more than a day from today is stale or hallucinated —
# the 2023-10-05 stamp on the poisoned brief would have been caught here.
def check_r12_header_date(rb: Runbook) -> list[Violation]:
    text = rb.raw or ""
    header = "\n".join(text.splitlines()[:_HEADER_LINES])
    m = _DATE_RE.search(header)
    if not m:
        return []
    try:
        d = date(int(m.group(1)), int(m.group(2)), int(m.group(3)))
    except ValueError:
        return [Violation(
            rule=12,
            location="document header",
            message=f"header date invalid: '{m.group(0)}'",
            fix="write a real calendar date in the header",
        )]
    delta = abs((date.today() - d).days)
    if delta > 1:
        return [Violation(
            rule=12,
            location="document header",
            message=f"header date mismatch: document dated {m.group(0)} "
                    f"({delta} days from today)",
            fix="date the document today, or state in the header why the "
                "date differs",
        )]
    return []


# ---------------------------------------------------------------------------
# R13 — Suspicious-character-count namesake (WARNING, heuristic)
# ---------------------------------------------------------------------------
# The namesake: a document whose total character count lands exactly on a
# "cute length" is a smell — a model gaming the length. Half joke, half
# real, so it reports as WARNING (listed, never fails the draft unless
# --strict), per the PARAM-PROOFIT-001 severity doctrine.
def check_r13_cute_length(rb: Runbook) -> list[Violation]:
    n = len(rb.raw or "")
    if n in CUTE_LENGTHS:
        return [Violation(
            rule=13,
            location="document",
            message=f"cute length: {n} chars ({CUTE_LENGTHS[n]}) — "
                    "a model gaming length is a smell",
            fix="add or remove substance so the length is incidental, "
                "not a namesake",
        )]
    return []


# ---------------------------------------------------------------------------
# R14 — Missing-file verification (ERROR, fail-closed)
# ---------------------------------------------------------------------------
# A claim that a file is missing is checkable: resolve it against the
# filesystem. If the file exists, the claim is a hallucination.
def check_r14_false_file_claims(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    for claimed, path, exists in _missing_file_claims(rb.raw or ""):
        if exists:
            out.append(Violation(
                rule=14,
                location="document",
                message=f"false file claim: '{claimed}' asserted missing "
                        f"but exists at {path}",
                fix="check the filesystem before claiming a file is missing — "
                    "a false missing claim is a hallucination",
            ))
    return out


ALL_1337_CHECKS = [
    check_r11_cross_role_dup,
    check_r12_header_date,
    check_r13_cute_length,
    check_r14_false_file_claims,
]
