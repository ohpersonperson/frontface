"""CAPTURE: append-only, timestamped raw records. Never interprets.

The isolation rule is enforced two ways:
1. Structural: ``capture()`` only ever appends. It has no code path that
   modifies, reorders, or deletes prior entries.
2. Heuristic: the entry text is scanned for interpretation markers
   (configurable; see ``config.MemoryConfig.interpretation_markers``).
   A hit raises ``InterpretationError`` unless the caller passes
   ``force=True``, in which case the bypass is recorded in the entry
   header — the exception is visible, never silent.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .adapters import StorageAdapter, default_adapter
from .config import MemoryConfig


class CaptureError(ValueError):
    """Base for capture failures."""


class InterpretationError(CaptureError):
    """The entry looks like synthesis, not capture. Move it to DISTILL."""


ENTRY_HEADER_PREFIX = "## "


def scan_interpretation(text: str, markers: tuple[str, ...]) -> list[str]:
    """Return the interpretation markers found in text (case-insensitive)."""
    lowered = text.lower()
    return [m for m in markers if m.lower() in lowered]


def stamp(now: datetime | None = None) -> str:
    dt = now or datetime.now().astimezone()
    return dt.strftime("%Y-%m-%d %H:%M %Z").strip()


@dataclass
class CaptureResult:
    domain: str
    path: str
    timestamp: str
    bytes_written: int
    bypassed_check: bool


def capture(
    config: MemoryConfig,
    domain: str,
    text: str,
    *,
    source: str = "",
    now: datetime | None = None,
    force: bool = False,
    adapter: StorageAdapter | None = None,
) -> CaptureResult:
    """Append one raw record to ``<domain>/raw.md``.

    Raises ``InterpretationError`` if the text trips an interpretation
    marker (unless ``force=True``), ``CaptureError`` on empty text or an
    unknown domain. Never touches any other file.
    """
    name = config.require_domain(domain)
    body = text.strip()
    if not body:
        raise CaptureError("Capture text must not be empty.")

    hits = scan_interpretation(body, config.interpretation_markers)
    if hits and not force:
        raise InterpretationError(
            f"Entry looks like interpretation, not capture — markers found: "
            f"{', '.join(hits)}. Rewrite as raw record, or pass force=True "
            f"to record the bypass explicitly."
        )

    ts = stamp(now)
    header = f"{ENTRY_HEADER_PREFIX}{ts}"
    if source.strip():
        header += f" — source: {source.strip()}"
    if hits:
        header += " — [interpretation-check bypassed: " + ", ".join(hits) + "]"
    entry = f"{header}\n\n{body}\n\n"

    store = adapter or default_adapter(config.root)
    path = f"{name}/raw.md"
    existed = store.exists(path)
    store.append(path, ("\n" if existed and not _ends_blank(store, path) else "") + entry)
    return CaptureResult(
        domain=name,
        path=path,
        timestamp=ts,
        bytes_written=len(entry.encode("utf-8")),
        bypassed_check=bool(hits),
    )


def _ends_blank(store: StorageAdapter, path: str) -> bool:
    text = store.read(path) or ""
    return text.endswith("\n\n") or not text


def read_raw(
    config: MemoryConfig,
    domain: str,
    *,
    adapter: StorageAdapter | None = None,
) -> str | None:
    """Return a domain's raw.md, or None if it has no captures yet."""
    name = config.require_domain(domain)
    store = adapter or default_adapter(config.root)
    return store.read(f"{name}/raw.md")


def route(kind: str) -> str:
    """The decision rule as a dispatch: recording→capture, consolidating→distill.

    ``kind`` must be exactly "capture" or "distill". Anything else —
    including "both" — raises, because the skill forbids performing both
    implicitly in one operation.
    """
    normalized = kind.strip().lower()
    if normalized == "capture":
        return "capture"
    if normalized == "distill":
        return "distill"
    raise CaptureError(
        f"Unknown operation {kind!r}: use 'capture' for recording new "
        f"information, 'distill' for consolidating existing information. "
        f"Never both in one operation."
    )
