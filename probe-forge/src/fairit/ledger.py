"""Append-only local ledger. Vendored per tool; stdlib only.

CANONICAL COPY: edit this file, then re-vendor with vendor.sh.
Do not edit the vendored copies in place.

Privacy rule (non-negotiable): the ledger NEVER stores raw input text.
Records carry SHA-256 digests of inputs plus structural summaries
(counts, verdicts, deltas). What happened, and what kind — never the words.

Location: ~/.frontface/<tool>/ledger.jsonl
  override: FRONTFACE_LEDGER_DIR=<dir>   (ledgers go to <dir>/<tool>/)
  disable:  FRONTFACE_NO_LEDGER=1         (record() becomes a silent no-op)

The ledger must never break the tool it serves: record() swallows OSError
and returns False instead of raising.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
from datetime import datetime, timezone

try:
    import fcntl
except ImportError:  # pragma: no cover — Windows has no fcntl
    fcntl = None  # type: ignore[assignment]


def _base_dir() -> str:
    return os.environ.get("FRONTFACE_LEDGER_DIR") or os.path.join(
        os.path.expanduser("~"), ".frontface"
    )


def _disabled() -> bool:
    return os.environ.get("FRONTFACE_NO_LEDGER") == "1"


class Ledger:
    """One JSONL ledger per tool. Cheap to construct; construct per use."""

    def __init__(self, tool: str) -> None:
        self.tool = tool
        self.dir = os.path.join(_base_dir(), tool)
        self.path = os.path.join(self.dir, "ledger.jsonl")

    @property
    def version(self) -> str:
        """The owning package's __version__, resolved lazily."""
        try:
            pkg = sys.modules.get(__package__ or "")
            return str(getattr(pkg, "__version__", "unknown"))
        except Exception:
            return "unknown"

    @staticmethod
    def digest(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()

    def record(
        self,
        event: str,
        summary: dict,
        *,
        input_text: str | None = None,
    ) -> bool:
        """Append one record. Returns False when disabled or on I/O error.

        Never raises. Never stores raw input text — only its digest.
        """
        if _disabled():
            return False
        rec: dict = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "tool": self.tool,
            "tool_version": self.version,
            "event": event,
            "summary": summary,
        }
        if input_text is not None:
            rec["input_digest"] = self.digest(input_text)
        try:
            os.makedirs(self.dir, exist_ok=True)
            with open(self.path, "a", encoding="utf-8") as f:
                if fcntl is not None:
                    fcntl.flock(f, fcntl.LOCK_EX)
                    try:
                        f.write(json.dumps(rec) + "\n")
                        f.flush()
                        os.fsync(f.fileno())
                    finally:
                        fcntl.flock(f, fcntl.LOCK_UN)
                else:
                    f.write(json.dumps(rec) + "\n")
        except OSError:
            return False
        return True

    def read(self, limit: int | None = None) -> list[dict]:
        """All records, oldest first. Empty list when there's no ledger."""
        try:
            with open(self.path, encoding="utf-8") as f:
                lines = f.read().splitlines()
        except OSError:
            return []
        recs = []
        for line in lines:
            line = line.strip()
            if line:
                try:
                    recs.append(json.loads(line))
                except ValueError:
                    continue  # never let a corrupt line kill the read
        return recs[-limit:] if limit else recs

    def summary(self) -> dict:
        """Counts by event plus first/last timestamps."""
        recs = self.read()
        by_event: dict[str, int] = {}
        for r in recs:
            ev = str(r.get("event", "?"))
            by_event[ev] = by_event.get(ev, 0) + 1
        return {
            "tool": self.tool,
            "records": len(recs),
            "events": by_event,
            "first": recs[0]["ts"] if recs else None,
            "last": recs[-1]["ts"] if recs else None,
        }
