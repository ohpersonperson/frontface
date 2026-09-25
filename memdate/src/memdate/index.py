"""INDEX: regenerate the cross-domain connective tissue.

Runs after any full or multi-domain distill. A single-domain distill
skips the index with a recorded reason — the procedure is mechanical
and the skip rule is code, not advice.

Body-text conventions the index understands (documented in the README):
- A line starting with ``? `` inside distilled.md is an uncertainty flag.
- A line starting with ``! `` is an explicit raw<->distilled divergence note.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from . import frontmatter as fm
from .adapters import StorageAdapter, default_adapter
from .config import MemoryConfig
from .distill import ARTIFACT as DISTILL_ARTIFACT, read_distilled

ARTIFACT = "memdate-cross-domain-index"
PROTOCOL_VERSION = "memdate/1.0.0"
INDEX_PATH = "INDEX-cross-domain.md"


class IndexError(ValueError):
    """Raised when the index cannot be built or verified."""


@dataclass
class IndexResult:
    path: str
    skipped: bool
    reason: str
    cross_domain_entities: int = 0
    open_questions: int = 0
    hot_zones: int = 0
    lifecycle: str = ""


def _uncertainty_flags(body: str) -> list[str]:
    return [ln[2:].strip() for ln in body.splitlines() if ln.startswith("? ")]


def _divergence_notes(body: str) -> list[str]:
    return [ln[2:].strip() for ln in body.splitlines() if ln.startswith("! ")]


def _chains(deps: dict[str, list[str]]) -> list[list[str]]:
    """Dependency paths of length >= 2 (the 'strongest chains' callout)."""
    found: list[list[str]] = []

    def walk(path: list[str]) -> None:
        nxt = deps.get(path[-1], [])
        for target in nxt:
            if target in path:
                continue
            new_path = path + [target]
            if len(new_path) >= 3:
                found.append(new_path)
            walk(new_path)

    for start in deps:
        walk([start])
    # Deduplicate while keeping order.
    seen: set[tuple[str, ...]] = set()
    unique: list[list[str]] = []
    for p in found:
        key = tuple(p)
        if key not in seen:
            seen.add(key)
            unique.append(p)
    return unique


def regenerate_index(
    config: MemoryConfig,
    touched: list[str],
    *,
    today: str | None = None,
    adapter: StorageAdapter | None = None,
) -> IndexResult:
    """Rebuild INDEX-cross-domain.md from every domain's distilled.md.

    ``touched`` is the list of domains the distill pass updated. Fewer
    than two distinct touched domains → the index is left alone and the
    skip is recorded in the returned result.
    """
    touched_names = sorted({config.require_domain(d) for d in touched})
    store = adapter or default_adapter(config.root)

    if len(touched_names) < 2:
        return IndexResult(
            path=INDEX_PATH,
            skipped=True,
            reason=(
                f"Single-domain distill ({', '.join(touched_names) or 'none'}): "
                f"index left untouched per the skip rule."
            ),
        )

    # 1. Collect.
    distilled: dict[str, tuple[dict[str, object], str]] = {}
    for domain in config.domains:
        parsed = read_distilled(config, domain, adapter=store)
        if parsed is not None:
            distilled[domain] = parsed
    if len(distilled) < 2:
        raise IndexError(
            f"Index needs at least two distilled domains; found "
            f"{len(distilled)} ({', '.join(sorted(distilled)) or 'none'}). "
            f"Distill more domains first."
        )

    # 2. Entities -> domains (cross-domain only).
    entity_domains: dict[str, list[str]] = {}
    entity_notes: dict[str, dict[str, str]] = {}
    for domain, (fields, _body) in distilled.items():
        for entity in _as_list(fields.get("entities")):
            entity_domains.setdefault(entity, []).append(domain)
        notes = fields.get("entity_notes")
        if isinstance(notes, dict):
            for entity, note in notes.items():
                entity_notes.setdefault(str(entity), {})[domain] = str(note)
    cross = {e: sorted(ds) for e, ds in entity_domains.items() if len(set(ds)) >= 2}

    # 3. Dependencies.
    deps: dict[str, list[str]] = {}
    for domain, (fields, _body) in distilled.items():
        informs = [d for d in _as_list(fields.get("informs")) if d in distilled]
        if informs:
            deps[domain] = sorted(set(informs))
    chains = _chains(deps)

    # 4. Open questions, prioritized by blast radius: questions sharing an
    #    entity with a cross-domain entity sort first.
    cross_lower = {e.lower() for e in cross}
    questions: list[tuple[str, str, bool]] = []  # (question, source, cross_domain)
    for domain, (fields, _body) in distilled.items():
        for q in _as_list(fields.get("open_questions")):
            ql = q.lower()
            hits_cross = any(e in ql for e in cross_lower)
            questions.append((q, domain, hits_cross))
    questions.sort(key=lambda item: (not item[2], item[1], item[0]))

    # 5. Hot zones.
    hot: list[str] = []
    for domain, (_fields, body) in distilled.items():
        for flag in _uncertainty_flags(body):
            hot.append(f"[{domain}] uncertainty: {flag}")
        for note in _divergence_notes(body):
            hot.append(f"[{domain}] raw<->distilled divergence: {note}")
    for entity, per_domain in entity_notes.items():
        if entity in cross and len(set(per_domain.values())) > 1:
            detail = "; ".join(f"{d}: {n}" for d, n in sorted(per_domain.items()))
            hot.append(f"[tension] {entity}: differing status notes — {detail}")

    # 6. Write.
    day = today or date.today().isoformat()
    lifecycle = "FINAL" if not questions else "ITERATIVE"
    lines: list[str] = []
    lines.append("# Cross-domain index")
    lines.append("")
    lines.append(f"_Regenerated {day} from {len(distilled)} distilled domains._")
    lines.append("")
    lines.append("## Entities -> Domains")
    lines.append("")
    if cross:
        for entity in sorted(cross):
            domains = cross[entity]
            note = ""
            per = entity_notes.get(entity, {})
            if per and len(set(per.values())) == 1:
                note = f" — {next(iter(per.values()))}"
            lines.append(f"- **{entity}**: {', '.join(domains)}{note}")
    else:
        lines.append("- _No entity is referenced in more than one domain yet._")
    lines.append("")
    lines.append("## Dependencies")
    lines.append("")
    if deps:
        for domain in sorted(deps):
            lines.append(f"- {domain} informs: {', '.join(deps[domain])}")
        if chains:
            lines.append("")
            lines.append("Strongest chains:")
            for chain in chains:
                lines.append(f"- {' -> '.join(chain)}")
    else:
        lines.append("- _No cross-domain dependencies declared yet._")
    lines.append("")
    lines.append("## Open Questions")
    lines.append("")
    if questions:
        for q, source, is_cross in questions:
            tag = " [cross-domain]" if is_cross else ""
            lines.append(f"- {q} (from {source}){tag}")
    else:
        lines.append("- _None._")
    lines.append("")
    lines.append("## Hot Zones")
    lines.append("")
    if hot:
        for item in hot:
            lines.append(f"- {item}")
    else:
        lines.append("- _None flagged._")
    lines.append("")

    doc = fm.render({
        "artifact": ARTIFACT,
        "date": day,
        "protocol": PROTOCOL_VERSION,
        "lifecycle": lifecycle,
    }) + "\n".join(lines)
    store.write(INDEX_PATH, doc)

    # 7. Verify: every indexed entity exists in >= 2 distilled files;
    #    every question traces to a distilled source. True by construction —
    #    assert it so a future refactor can't silently break the invariant.
    for entity, domains in cross.items():
        count = sum(
            1 for d in domains
            if entity in _as_list(distilled[d][0].get("entities"))
        )
        assert count >= 2, f"orphan entity in index: {entity}"
    for _q, source, _c in questions:
        assert source in distilled, f"orphan question source: {source}"

    return IndexResult(
        path=INDEX_PATH,
        skipped=False,
        reason=f"Regenerated from {len(distilled)} distilled domains.",
        cross_domain_entities=len(cross),
        open_questions=len(questions),
        hot_zones=len(hot),
        lifecycle=lifecycle,
    )


def _as_list(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(v) for v in value]
    return []


def read_index(
    config: MemoryConfig,
    *,
    adapter: StorageAdapter | None = None,
) -> tuple[dict[str, object], str] | None:
    """Return ``(frontmatter, body)`` for INDEX-cross-domain.md, or None."""
    store = adapter or default_adapter(config.root)
    text = store.read(INDEX_PATH)
    if text is None:
        return None
    fields, body = fm.split(text)
    fm.require(fields, "artifact", "date", "protocol", "lifecycle", what="index")
    if fields.get("artifact") != ARTIFACT:
        raise IndexError(
            f"Index artifact is {fields.get('artifact')!r}, expected {ARTIFACT!r}."
        )
    return fields, body
