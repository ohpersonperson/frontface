"""Template-shaped Markdown parser for runbook drafts.

This is not a general Markdown parser. It understands exactly one document
shape: the proofit runbook template (see templates/runbook-template.md),
which mirrors the skill's own Output Format section:

  Ground Rules & Prerequisites / Step-by-Step Directives / Validation & Closure

Steps are `### Step N: name` headings with **Do:** / **Look for:** /
**Verify:** / **If wrong:** / **Fix:** fields. Service routing specs are
`### <service name>` headings inside the prerequisites section.
"""
from __future__ import annotations

import re

from .model import Runbook, ServiceSpec, Step

HEADING_RE = re.compile(r"^(#{1,6})\s+(.*?)\s*$")
FIELD_RE = re.compile(
    r"^\s*\*{0,2}(Do|Look for|Verify|If wrong|Fix)\s*:\*{0,2}\s*(.*)$",
    re.IGNORECASE,
)
STEP_RE = re.compile(r"^step\s+(\d+)\s*:?\s*(.*)$", re.IGNORECASE)

# Subsection headings inside Ground Rules & Prerequisites that are NOT services.
KNOWN_PREREQ_SUBSECTIONS = [
    r"required baseline",
    r"starting state",
    r"precondition",
    r"routing architecture",
    r"input spec",
    r"rate limit",
    r"error path",
    r"needed tools",
    r"required tools",
    r"needed items",
    r"expected outcome",
]


def classify_section(title: str) -> str:
    t = title.lower()
    if re.search(r"prereq|ground rules", t):
        return "prereq"
    if re.search(r"step.by.step|directives", t):
        return "steps"
    if re.search(r"valid|closure|success condition|consistency", t):
        return "validation"
    if re.search(r"glossar|\bterms\b|definitions", t):
        return "glossary"
    return "other"


def _is_known_prereq_subsection(title: str) -> bool:
    t = title.lower()
    return any(re.search(p, t) for p in KNOWN_PREREQ_SUBSECTIONS)


def _is_step_heading(title: str) -> bool:
    return bool(STEP_RE.match(title.strip()))


def parse(text: str) -> Runbook:
    rb = Runbook(raw=text)
    lines = text.splitlines()

    current_section: str | None = None
    current_step: Step | None = None
    current_field: str | None = None
    current_service: ServiceSpec | None = None
    # raw-text accumulators per top-level section
    section_texts: dict[str, list[str]] = {}

    def flush_step():
        nonlocal current_step, current_field
        if current_step is not None:
            rb.steps.append(current_step)
            current_step = None
            current_field = None

    def flush_service():
        nonlocal current_service
        if current_service is not None:
            rb.services.append(current_service)
            current_service = None

    for i, line in enumerate(lines, start=1):
        m = HEADING_RE.match(line)
        if m:
            level = len(m.group(1))
            title = m.group(2).strip()
            flush_step()
            flush_service()
            current_field = None
            if level <= 2:
                current_section = classify_section(title)
                rb.section_order.append((current_section, title, i))
                section_texts.setdefault(current_section, [])
            elif current_section == "steps" and _is_step_heading(title):
                sm = STEP_RE.match(title.strip())
                current_step = Step(
                    number=int(sm.group(1)),
                    name=sm.group(2).strip(),
                    line_no=i,
                )
                rb.steps_present = True
            elif current_section in ("prereq", "glossary"):
                if _is_known_prereq_subsection(title):
                    current_section = "prereq"
                elif re.search(r"glossar|\bterms\b|definitions", title, re.I):
                    current_section = "glossary"
                    rb.section_order.append(("glossary", title, i))
                    section_texts.setdefault("glossary", [])
                elif current_section == "prereq":
                    # A named service routing block.
                    current_service = ServiceSpec(name=title, line_no=i)
            # record raw text under the current top-level section
            if current_section:
                section_texts.setdefault(current_section, []).append(line)
            continue

        if current_step is not None:
            fm = FIELD_RE.match(line)
            if fm:
                fname = fm.group(1).lower().replace(" ", "_")
                current_field = fname
                setattr(current_step, fname, fm.group(2).strip())
                continue
            if current_field and line.strip():
                # continuation of the current field
                prev = getattr(current_step, current_field)
                setattr(current_step, current_field, (prev + " " + line.strip()).strip())
                continue
            continue

        if current_service is not None:
            current_service.body += line + "\n"
            continue

        if current_section:
            section_texts.setdefault(current_section, []).append(line)

    flush_step()
    flush_service()

    rb.prereq_text = "\n".join(section_texts.get("prereq", []))
    rb.prereq_present = any(k == "prereq" for k, _, _ in rb.section_order)
    rb.validation_text = "\n".join(section_texts.get("validation", []))
    rb.validation_present = any(k == "validation" for k, _, _ in rb.section_order)
    rb.glossary_text = "\n".join(section_texts.get("glossary", []))
    rb.glossary_present = any(k == "glossary" for k, _, _ in rb.section_order)
    return rb
