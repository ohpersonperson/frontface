"""DISTILL: consolidate raw into derived distilled.md. Never touches raw.

The caller (human or model) supplies the consolidated body; the library
writes it with provenance frontmatter and enforces the isolation rule by
checksumming raw.md before and after the write. If raw changed in
between, the run fails — DISTILL never alters raw, and it refuses to
certify a run where something else did.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date

from . import frontmatter as fm
from .adapters import StorageAdapter, default_adapter
from .config import MemoryConfig

ARTIFACT = "memdate-distilled"
PROTOCOL_VERSION = "memdate/1.0.0"

LIFECYCLES = ("INITIAL", "ITERATIVE", "FINAL")
# FINAL only if the domain's raw record is fully consolidated with no open threads.


class DistillError(ValueError):
    """Raised when a distill run breaks the isolation rules."""


@dataclass
class DistillResult:
    domain: str
    path: str
    lifecycle: str
    raw_untouched: bool
    entities: tuple[str, ...] = ()
    open_questions: tuple[str, ...] = ()


def distill(
    config: MemoryConfig,
    domain: str,
    body: str,
    *,
    entities: list[str] | None = None,
    entity_notes: dict[str, str] | None = None,
    informs: list[str] | None = None,
    open_questions: list[str] | None = None,
    lifecycle: str = "ITERATIVE",
    today: str | None = None,
    adapter: StorageAdapter | None = None,
) -> DistillResult:
    """Write ``<domain>/distilled.md`` with provenance frontmatter.

    - ``body`` is the consolidated synthesis (supplied by the caller).
    - ``entities`` names people/places/concepts this distillation
      references; the cross-domain index uses them. ``entity_notes`` maps
      an entity to a one-line status note.
    - ``informs`` lists other domains this domain's material informs
      (dependency direction).
    - ``open_questions`` are contradictions/unknowns visible in this domain.
    - Raises ``DistillError`` if raw.md is missing (nothing to distill),
      if lifecycle is invalid, or if raw.md's bytes changed during the run.
    """
    name = config.require_domain(domain)
    text = body.strip()
    if not text:
        raise DistillError("Distilled body must not be empty.")
    cycle = lifecycle.strip().upper()
    if cycle not in LIFECYCLES:
        raise DistillError(
            f"Invalid lifecycle {lifecycle!r}. Use one of: {', '.join(LIFECYCLES)}."
        )
    if informs:
        for other in informs:
            config.require_domain(other)

    store = adapter or default_adapter(config.root)
    raw_path = f"{name}/raw.md"
    raw_text = store.read(raw_path)
    if raw_text is None:
        raise DistillError(
            f"Cannot distill domain {name!r}: no raw.md exists. "
            f"Capture something first."
        )
    raw_before = store.digest(raw_path)

    fields: dict[str, object] = {
        "artifact": ARTIFACT,
        "domain": name,
        "date": today or date.today().isoformat(),
        "protocol": PROTOCOL_VERSION,
        "lifecycle": cycle,
        "entities": [e.strip() for e in (entities or []) if e.strip()],
        "informs": [config.require_domain(d) for d in (informs or [])],
        "open_questions": [q.strip() for q in (open_questions or []) if q.strip()],
    }
    if entity_notes:
        fields["entity_notes"] = {k.strip(): v.strip() for k, v in entity_notes.items()}

    document = fm.render(fields) + text.rstrip() + "\n"
    distilled_path = f"{name}/distilled.md"
    store.write(distilled_path, document)

    raw_after = store.digest(raw_path)
    if raw_after != raw_before:
        raise DistillError(
            f"Isolation violation: {raw_path} changed during the distill run. "
            f"DISTILL never alters raw — the run is void; inspect what wrote to raw."
        )

    return DistillResult(
        domain=name,
        path=distilled_path,
        lifecycle=cycle,
        raw_untouched=True,
        entities=tuple(fields["entities"]),  # type: ignore[arg-type]
        open_questions=tuple(fields["open_questions"]),  # type: ignore[arg-type]
    )


def read_distilled(
    config: MemoryConfig,
    domain: str,
    *,
    adapter: StorageAdapter | None = None,
) -> tuple[dict[str, object], str] | None:
    """Return ``(frontmatter, body)`` for a domain's distilled.md, or None."""
    name = config.require_domain(domain)
    store = adapter or default_adapter(config.root)
    text = store.read(f"{name}/distilled.md")
    if text is None:
        return None
    fields, body = fm.split(text)
    fm.require(fields, "artifact", "domain", "date", "protocol", "lifecycle",
               what=f"distilled.md for {name!r}")
    if fields.get("artifact") != ARTIFACT:
        raise DistillError(
            f"distilled.md for {name!r} has artifact {fields.get('artifact')!r}, "
            f"expected {ARTIFACT!r}."
        )
    return fields, body
