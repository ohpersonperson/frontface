"""The ten proofit rules as code.

Each check takes a parsed Runbook and returns a list of Violations.
Under fail-closed semantics every violation is an ERROR: any one of them
rejects the draft.

Implementation status per rule:
  full check : R2, R3, R4, R6, R7, R9, R10  (mechanical structure/schema)
  heuristic  : R1, R8                     (narrow phrase lists — tripwires)
  convention : R5                         (enforces the Term (definition)
                                           pattern where a glossary exists;
                                           detecting undefined jargon without
                                           a glossary is out of scope)
"""
from __future__ import annotations

import re

from .model import Runbook, Violation


def _has_label(text: str) -> bool:
    """Does the line name a visible label (bold, quotes, or code)?"""
    return bool(
        re.search(r"\*\*.+?\*\*|\"[^\"]+\"|'[^']+'|`[^`]+`", text)
    )


def _strip_labels(text: str) -> str:
    text = re.sub(r"\*\*(.+?)\*\*", " ", text)
    text = re.sub(r'"[^"]+"', " ", text)
    text = re.sub(r"'[^']+'", " ", text)
    text = re.sub(r"`[^`]+`", " ", text)
    return text


def _word_in(text: str, words: list[str]) -> bool:
    t = text.lower()
    return any(re.search(r"\b" + re.escape(w) + r"\b", t) for w in words)


# ---------------------------------------------------------------------------
# R1 — Remove every assumption (heuristic, narrow)
# ---------------------------------------------------------------------------
# Fires only on clear hits: bare unlabeled directives ("Press Continue"),
# and claims that something happens on its own ("is done automatically").
# It cannot prove completeness — a linter can't know which assumptions the
# author silently held. Kept narrow on purpose: under fail-closed a
# false positive blocks a good draft.
R1_BARE_DIRECTIVES = [
    "press continue",
    "click continue",
    "select the option",
    "click ok",
    "press ok",
]
# "is generated automatically" / "are handled automatically" — a claim that
# something happens on its own. Deliberately requires is/are/was/were so that
# plain state-change descriptions ("the download begins") don't trip it.
R1_AUTOMATICITY_RE = re.compile(
    r"\b(is|are|was|were)\b[^.\n]{0,40}\bautomatically\b", re.IGNORECASE
)


def check_r1_assumptions(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    for step in rb.steps:
        for field_name in ("do", "look_for"):
            line = getattr(step, field_name)
            if not line:
                continue
            low = line.lower()
            if R1_AUTOMATICITY_RE.search(line):
                out.append(Violation(
                    rule=1,
                    location=f"Step {step.number} ({field_name})",
                    message=f'assumes automatic behavior: "{line.strip()}"',
                    fix="state the condition explicitly instead of assuming it happens on its own",
                ))
                continue
            if not _has_label(line):
                for phrase in R1_BARE_DIRECTIVES:
                    if phrase in low:
                        out.append(Violation(
                            rule=1,
                            location=f"Step {step.number} ({field_name})",
                            message=f'unlabeled directive assumes the reader knows where/what: "{line.strip()}"',
                            fix="name the exact visible label, e.g. the blue **Continue** button in the bottom-right corner",
                        ))
                        break
    return out


# ---------------------------------------------------------------------------
# R2 — Define every requirement before starting (structure)
# ---------------------------------------------------------------------------
PREREQ_FIELDS: list[tuple[str, list[str]]] = [
    ("hardware", ["hardware", "computer", "laptop", "device", "machine"]),
    ("software", ["software", "browser", "app", "apps", "application", "program"]),
    ("accounts", ["account", "accounts"]),
    ("permissions", ["permission", "permissions", "admin", "access level"]),
    ("files", ["file", "files"]),
    ("internet access", ["internet", "wi-fi", "wifi", "online", "connection"]),
    ("free-tier limits", ["limit", "limits", "quota", "rate limit",
                         "per day", "per month", "per hour"]),
    ("starting state", ["starting state", "baseline", "precondition", "preconditions",
                        "starting condition"]),
]


def check_r2_prerequisites(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    if not rb.prereq_present:
        out.append(Violation(
            rule=2,
            location="document",
            message="no Ground Rules & Prerequisites section found",
            fix="add a Ground Rules & Prerequisites section before the first step, covering all eight required fields",
        ))
        return out
    kinds = [k for k, _, _ in rb.section_order]
    if "steps" in kinds and kinds.index("prereq") > kinds.index("steps"):
        out.append(Violation(
            rule=2,
            location="document",
            message="prerequisites section comes after the steps — requirements must be defined before step 1",
            fix="move Ground Rules & Prerequisites above Step-by-Step Directives",
        ))
    for field_name, keywords in PREREQ_FIELDS:
        # Free-tier limits may live in the per-service routing specs, which
        # are part of the prerequisites section — count those too.
        haystack = rb.prereq_text
        if field_name == "free-tier limits":
            haystack += " " + " ".join(s.body for s in rb.services)
        if not _word_in(haystack, keywords):
            out.append(Violation(
                rule=2,
                location="Ground Rules & Prerequisites",
                message=f"required prerequisite field missing: {field_name}",
                fix=f"state the {field_name} requirement explicitly (never reveal new prerequisites mid-guide)",
            ))
    return out


# ---------------------------------------------------------------------------
# R3 — One action per step (structure — the strongest check)
# ---------------------------------------------------------------------------
ACTION_VERBS = [
    "open", "click", "press", "select", "type", "enter", "copy", "paste",
    "save", "run", "launch", "close", "download", "upload", "install",
    "uninstall", "delete", "create", "rename", "move", "wait", "check",
    "read", "write", "send", "start", "stop", "restart", "log", "sign",
    "navigate", "go", "scroll", "drag", "drop", "choose", "pick", "set",
    "change", "fill", "submit", "confirm", "cancel", "switch", "export", "load",
    "import", "print", "refresh",
]
_SPLIT_RE = re.compile(r"\s+and\s+|\s*,\s*then\s+|\s+then\s+|\s*;\s*")


def _verb_led(fragment: str) -> bool:
    words = re.findall(r"[A-Za-z']+", fragment)
    if not words:
        return False
    # crude stemming so "clicks" matches "click" ("go" keeps its form)
    stem = words[0].lower()
    if stem.endswith("s") and stem[:-1] in ACTION_VERBS:
        stem = stem[:-1]
    return stem in ACTION_VERBS


def _count_actions(do_text: str) -> int:
    fragments = [f for f in _SPLIT_RE.split(do_text) if f.strip()]
    return sum(1 for f in fragments if _verb_led(f))


def check_r3_one_action(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    if not rb.steps:
        out.append(Violation(
            rule=3,
            location="Step-by-Step Directives",
            message="no steps found — the directives section is missing or empty",
            fix="write the workflow as numbered steps, one action each",
        ))
        return out
    numbers = [s.number for s in rb.steps]
    if numbers != list(range(1, len(numbers) + 1)):
        out.append(Violation(
            rule=3,
            location="Step-by-Step Directives",
            message=f"step numbers are not sequential 1..{len(numbers)}: {numbers}",
            fix="renumber steps sequentially starting at 1",
        ))
    for step in rb.steps:
        if not step.do.strip():
            out.append(Violation(
                rule=3,
                location=f"Step {step.number}",
                message="step has no Do: field — zero actions is not one action",
                fix="write exactly one action in a Do: field",
            ))
            continue
        n = _count_actions(step.do)
        if n > 1:
            out.append(Violation(
                rule=3,
                location=f"Step {step.number}",
                message=f'{n} actions in one Do: "{step.do.strip()}"',
                fix="split into separate steps, one action each",
            ))
    return out


# ---------------------------------------------------------------------------
# R4 — Use concrete references (phrase + format)
# ---------------------------------------------------------------------------
# Fires only on BARE nouns — "the button", "the dialog" — the skill's own
# bad examples. A noun with a qualifier ("a confirmation dialog", "the VS
# Code window", "the blue Publish button") names something distinguishable
# and does not fire. "window"/"screen" are excluded: they almost always
# carry a product name ("the Settings window").
UI_NOUNS = ["button", "link", "menu", "tab", "dialog", "field", "icon",
            "dropdown", "checkbox", "option"]
_BARE_UI_RE = re.compile(
    r"\b(the|a|an)\s+(button|link|menu|tab|dialog|field|icon|dropdown|checkbox|option)\b",
    re.IGNORECASE,
)
_QUALIFIED_UI_RE = re.compile(
    r"\b(the|a|an)\s+[A-Za-z]+\s+(button|link|menu|tab|dialog|field|icon|dropdown|checkbox|option)\b",
    re.IGNORECASE,
)
R4_VAGUE = ["select the file", "open the file"]


def check_r4_concrete_refs(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    for step in rb.steps:
        for field_name in ("do", "look_for"):
            line = getattr(step, field_name)
            if not line:
                continue
            low = line.lower()
            if _has_label(line):
                continue
            if _BARE_UI_RE.search(line) and not _QUALIFIED_UI_RE.search(line):
                out.append(Violation(
                    rule=4,
                    location=f"Step {step.number} ({field_name})",
                    message=f'UI element named without a visible label: "{line.strip()}"',
                    fix="quote or bold the exact visible label, e.g. the **Save** button",
                ))
                continue
            for phrase in R4_VAGUE:
                if phrase in low and "named" not in low:
                    out.append(Violation(
                        rule=4,
                        location=f"Step {step.number} ({field_name})",
                        message=f'vague reference with no label: "{line.strip()}"',
                        fix="name the exact item, e.g. the file named **report.xlsx**",
                    ))
                    break
    return out


# ---------------------------------------------------------------------------
# R5 — Explain unavoidable technical terms (convention)
# ---------------------------------------------------------------------------
# Enforces the `Term (definition)` pattern where a glossary exists.
# Detecting undefined jargon WITHOUT a glossary needs a glossary or a
# model — that judgment is explicitly out of scope (see README).
TERM_DEF_RE = re.compile(r"^\s*[-*]?\s*.+\([^)]+\)\s*$")


def check_r5_terms(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    if not rb.glossary_present:
        return out
    for i, line in enumerate(rb.glossary_text.splitlines(), start=1):
        s = line.strip()
        if not s or s.startswith("#"):
            continue
        if not TERM_DEF_RE.match(s):
            out.append(Violation(
                rule=5,
                location=f"glossary (line {i})",
                message=f'term without an inline definition: "{s}"',
                fix="use the Term (definition) pattern, e.g. Repository (a folder that stores the project's files and history)",
            ))
    return out


# ---------------------------------------------------------------------------
# R6 — Verification after every milestone (structure)
# ---------------------------------------------------------------------------
OBSERVABLE = ["display", "displays", "appear", "appears", "exist", "exists",
              "contain", "contains", "show", "shows", "return", "returns",
              "match", "matches", "visible", "checkmark", "present",
              "created", "saved", "opens"]


def check_r6_verification(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    for step in rb.steps:
        if not step.verify.strip():
            out.append(Violation(
                rule=6,
                location=f"Step {step.number}",
                message="step ends without a Verify: block",
                fix="describe exactly what should be observed, e.g. Verify: the file now exists at ~/backup/",
            ))
        elif not _word_in(step.verify, OBSERVABLE):
            out.append(Violation(
                rule=6,
                location=f"Step {step.number} (Verify)",
                message=f'verification is not objectively checkable: "{step.verify.strip()}"',
                fix="describe something observable — what the screen displays, what exists, what the output contains",
            ))
    return out


# ---------------------------------------------------------------------------
# R7 — Include immediate recovery (structure)
# ---------------------------------------------------------------------------
def check_r7_recovery(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    for step in rb.steps:
        if not step.if_wrong.strip():
            out.append(Violation(
                rule=7,
                location=f"Step {step.number}",
                message="step has no If wrong: block — the most likely mistake is unstated",
                fix="add If wrong: describing the most likely mistake for this step",
            ))
        if not step.fix.strip():
            out.append(Violation(
                rule=7,
                location=f"Step {step.number}",
                message="step has no Fix: block — no recovery path",
                fix="add Fix: with the shortest recovery path (resume the guide, don't restart, when possible)",
            ))
    return out


# ---------------------------------------------------------------------------
# R8 — Never skip state changes (heuristic, narrow)
# ---------------------------------------------------------------------------
# A linter cannot know what state changes a step *causes* — that needs the
# author or a model. This is a tripwire: when the Do: line starts with a
# state-changing verb, the Look for:/Verify: text must describe the resulting
# state in transition language. Narrow by design.
STATE_VERBS = ["open", "close", "launch", "start", "restart", "install",
               "uninstall", "delete", "download", "upload", "submit",
               "refresh", "navigate", "log", "sign"]
TRANSITIONS = ["opens", "appears", "closes", "begins", "starts", "dialog",
               "new tab", "window", "confirmation", "downloads", "downloaded",
               "installed", "deleted", "submitted", "refreshed", "logged in",
               "logged out", "signed in", "signed out"]


def check_r8_state_changes(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    for step in rb.steps:
        words = re.findall(r"[A-Za-z']+", step.do)
        if not words:
            continue
        first = words[0].lower()
        if first not in STATE_VERBS:
            continue
        observed = (step.look_for + " " + step.verify).lower()
        if not any(t in observed for t in TRANSITIONS):
            out.append(Violation(
                rule=8,
                location=f"Step {step.number}",
                message=f'state-changing action with no described state change: "{step.do.strip()}"',
                fix="describe what the software visibly does — a new tab opens, a dialog appears, the window closes",
            ))
    return out


# ---------------------------------------------------------------------------
# R9 — Specify routing decisions upfront (schema)
# ---------------------------------------------------------------------------
SERVICE_ITEMS: list[tuple[str, list[str]]] = [
    ("when to use", ["when to use", "use when", "trigger", "condition", "route to", "use for"]),
    ("free-tier limits", ["limit", "limits", "quota", "rate limit", "context window"]),
    ("verbatim prompt", ["prompt"]),
    ("expected output format", ["output format", "expected output", "schema", "response format"]),
]


def check_r9_routing(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    if not rb.services:
        return out  # single-service workflow: routing spec is vacuous
    for svc in rb.services:
        for item_name, keywords in SERVICE_ITEMS:
            if not _word_in(svc.body, keywords):
                out.append(Violation(
                    rule=9,
                    location=f"Routing / {svc.name}",
                    message=f"service spec missing: {item_name}",
                    fix=f"specify {item_name} for {svc.name} — no improvisation mid-workflow",
                ))
    if not _word_in(rb.prereq_text, ["rate limit handling", "when hitting", "quota exhaust"]):
        out.append(Violation(
            rule=9,
            location="Routing Architecture",
            message="no rate-limit handling — what to do when a free-tier limit is hit is unstated",
            fix="add rate limit handling: wait time, fallback service, or graceful degradation",
        ))
    if not _word_in(rb.prereq_text, ["error path", "error paths", "if any service fails",
                                   "unexpected data", "service fails"]):
        out.append(Violation(
            rule=9,
            location="Routing Architecture",
            message="no error paths — what to do if a service fails or returns unexpected data is unstated",
            fix="add error paths per service",
        ))
    return out


# ---------------------------------------------------------------------------
# R10 — Finish with full validation (structure)
# ---------------------------------------------------------------------------
def check_r10_validation(rb: Runbook) -> list[Violation]:
    out: list[Violation] = []
    if not rb.validation_present:
        out.append(Violation(
            rule=10,
            location="document",
            message="no Validation & Closure section — the document never describes the completed state",
            fix="end with Validation & Closure: a Success Condition plus consistency checkpoints",
        ))
        return out
    kinds = [k for k, _, _ in rb.section_order]
    # A trailing glossary is fine — the rule is "never end on an action".
    if kinds and kinds[-1] not in ("validation", "glossary"):
        out.append(Violation(
            rule=10,
            location="document",
            message="document does not end with Validation & Closure — it ends on an action",
            fix="move Validation & Closure to the end; never end with the final action",
        ))
    # A Step N heading placed after the validation section means the
    # document ends on an action even if a validation section exists.
    val_pos = None
    for m in re.finditer(r"^#{1,6}\s+.*$", rb.raw, re.M):
        if re.search(r"valid|closure|success condition|consistency", m.group(0), re.I):
            val_pos = m.start()
    if val_pos is not None:
        for m in re.finditer(r"^#{1,6}\s+step\s+\d+", rb.raw, re.M | re.I):
            if m.start() > val_pos:
                out.append(Violation(
                    rule=10,
                    location="document",
                    message="a step appears after Validation & Closure — the document ends on an action",
                    fix="move all steps above Validation & Closure",
                ))
                break
    if not _word_in(rb.validation_text, ["success condition"]):
        out.append(Violation(
            rule=10,
            location="Validation & Closure",
            message="no Success Condition — the exact final state is undescribed",
            fix="describe the exact final state so success is certain, not hoped for",
        ))
    has_checklist = bool(re.search(r"^\s*-\s*\[[ xX]\]", rb.validation_text, re.M))
    has_list = bool(re.search(r"^\s*(?:-\s+|\*\s+|\d+\.\s+)\S", rb.validation_text, re.M))
    if not has_checklist and not has_list:
        out.append(Violation(
            rule=10,
            location="Validation & Closure",
            message="no consistency checklist — nothing to check the workflow against",
            fix="add consistency checkpoints: inputs met spec, prompts correct, outputs matched format",
        ))
    return out


ALL_CHECKS = [
    check_r1_assumptions,
    check_r2_prerequisites,
    check_r3_one_action,
    check_r4_concrete_refs,
    check_r5_terms,
    check_r6_verification,
    check_r7_recovery,
    check_r8_state_changes,
    check_r9_routing,
    check_r10_validation,
]
