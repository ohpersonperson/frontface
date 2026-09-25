"""DROP: the ingestion layer.

Files land in ``DROP/NEW/`` from anywhere — a phone note, an export, a
paste. ``sweep_new()`` routes each one: a leading ``domain: <name>``
line decides the destination; files with no routable domain, an unknown
domain, or interpretation markers go to ``DROP/QUARANTINE/`` instead of
being silently captured. Captured files move to ``DROP/PROCESSED/`` with
a timestamp prefix. Nothing is ever deleted by the sweep.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .adapters import StorageAdapter, default_adapter
from .capture import CaptureError, InterpretationError, capture, scan_interpretation
from .config import ConfigError, MemoryConfig


@dataclass
class SweepItem:
    filename: str
    outcome: str  # "captured" | "quarantined"
    domain: str = ""
    reason: str = ""


def ensure_layout(
    config: MemoryConfig,
    *,
    adapter: StorageAdapter | None = None,
) -> None:
    """Create the root, DROP subdirs, and per-domain directories."""
    store = adapter or default_adapter(config.root)
    store.makedirs("")
    for sub in config.drop_subdirs:
        store.makedirs(f"DROP/{sub}")
    for domain in config.domains:
        store.makedirs(domain)


def sweep_new(
    config: MemoryConfig,
    *,
    now: datetime | None = None,
    adapter: StorageAdapter | None = None,
) -> list[SweepItem]:
    """Route every file in DROP/NEW/. Returns one item per file."""
    store = adapter or default_adapter(config.root)
    ensure_layout(config, adapter=store)
    ts = (now or datetime.now().astimezone()).strftime("%Y%m%d-%H%M%S")
    results: list[SweepItem] = []

    for filename in store.list_files("DROP/NEW"):
        src = f"DROP/NEW/{filename}"
        text = store.read(src) or ""
        domain, body = _split_domain_header(text)

        if not domain:
            _quarantine(store, src, filename, ts,
                        "no 'domain: <name>' header on the first line")
            results.append(SweepItem(filename, "quarantined",
                                     reason="missing domain header"))
            continue
        try:
            name = config.require_domain(domain)
        except ConfigError:
            _quarantine(store, src, filename, ts,
                        f"unknown domain {domain!r}")
            results.append(SweepItem(filename, "quarantined",
                                     reason=f"unknown domain {domain!r}"))
            continue
        if not body.strip():
            _quarantine(store, src, filename, ts, "empty body after header")
            results.append(SweepItem(filename, "quarantined",
                                     reason="empty body"))
            continue
        hits = scan_interpretation(body, config.interpretation_markers)
        if hits:
            _quarantine(store, src, filename, ts,
                        f"interpretation markers: {', '.join(hits)}")
            results.append(SweepItem(filename, "quarantined",
                                     domain=name,
                                     reason="interpretation markers"))
            continue
        try:
            result = capture(config, name, body,
                             source=f"DROP/NEW/{filename}",
                             now=now, adapter=store)
        except (CaptureError, InterpretationError) as exc:
            _quarantine(store, src, filename, ts, str(exc))
            results.append(SweepItem(filename, "quarantined",
                                     domain=name, reason=str(exc)))
            continue
        store.move(src, f"DROP/PROCESSED/{ts}-{filename}")
        results.append(SweepItem(filename, "captured", domain=result.domain))
    return results


def _split_domain_header(text: str) -> tuple[str, str]:
    """Split an optional leading ``domain: <name>`` line from the body."""
    lines = text.splitlines()
    if not lines:
        return "", ""
    first = lines[0].strip()
    if first.lower().startswith("domain:"):
        return first.split(":", 1)[1].strip(), "\n".join(lines[1:])
    return "", text


def _quarantine(store: StorageAdapter, src: str, filename: str,
                ts: str, reason: str) -> None:
    store.write(f"DROP/QUARANTINE/{ts}-{filename}.reason.txt",
                f"Quarantined {ts}: {reason}\n")
    store.move(src, f"DROP/QUARANTINE/{ts}-{filename}")
