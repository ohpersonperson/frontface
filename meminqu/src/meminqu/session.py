"""The interview session: domain walk, capture calls, completion report.

The session is the record-keeping side of the interview. The actual
questions and answers happen outside it (an operator or a model runs
the conversation); this class tracks state — which domain is active,
which registers were suggested, what got captured, what got skipped —
formats entries, and makes the capture calls into memdate.

The domain list is inherited from the memdate config. This
package declares no domains of its own: single source of truth.
"""

from __future__ import annotations

try:
    from memdate import (
        CaptureResult,
        InterpretationError,
        MemoryConfig,
        StorageAdapter,
        capture,
    )
except ImportError as exc:  # pragma: no cover - dependency wiring
    raise ImportError(
        "meminqu requires the memdate package "
        "(the memdate module). Install it first, e.g.: "
        "pip install -e ../memdate   # from this staging tree"
    ) from exc

from .entry import Response, format_entry
from .registers import REGISTERS, Register, plan_cycle


class SessionError(ValueError):
    """Raised for bad session operations (unknown domain, bad order, ...)."""


class InterviewSession:
    """One guided-capture interview cycle over a memory store's domains."""

    SOURCE_TAG = "meminqu"

    def __init__(
        self,
        config: MemoryConfig,
        *,
        adapter: StorageAdapter | None = None,
        per_domain: int = 3,
        registers: tuple[Register, ...] = REGISTERS,
        domains: tuple[str, ...] | list[str] | None = None,
    ) -> None:
        self.config = config
        self.adapter = adapter
        # Domains come from the config unless the caller narrows the
        # cycle to a subset (which must still be config-known domains).
        chosen = tuple(domains) if domains is not None else config.domains
        for d in chosen:
            config.require_domain(d)
        self.domains: tuple[str, ...] = chosen
        self.register_plan = plan_cycle(self.domains, per_domain, registers)
        self._captured: dict[str, CaptureResult] = {}
        self._skipped: list[str] = []
        self._started: list[str] = []

    # -- interview flow -------------------------------------------------

    def start_domain(self, domain: str) -> list[str]:
        """Announce a domain; return its suggested registers."""
        name = self.config.require_domain(domain)
        if name not in self.domains:
            raise SessionError(f"Domain {domain!r} is not in this cycle.")
        if name not in self._started:
            self._started.append(name)
        return list(self.register_plan[name])

    def submit_answers(
        self,
        domain: str,
        responses: list[Response],
        *,
        capture_domain: str | None = None,
    ) -> CaptureResult:
        """Format the answers and capture them via memdate.

        Captures under the announced domain unless ``capture_domain``
        is given — the explicit reassignment the skill requires before
        material may land in a different domain's raw.md.

        Answers are captured under memdate's pure CAPTURE rules:
        if an answer trips an interpretation marker, capture() raises
        InterpretationError rather than silently synthesizing. That is
        enforcement, not a bug — rewrite the answer as raw record, or
        pass force through the lower-level capture() yourself.
        """
        name = self.config.require_domain(domain)
        target = (
            self.config.require_domain(capture_domain)
            if capture_domain is not None
            else name
        )
        body = format_entry(name, responses)
        result = capture(
            self.config,
            target,
            body,
            source=self.SOURCE_TAG,
            adapter=self.adapter,
        )
        self._captured[name] = result
        return result

    def skip_domain(self, domain: str) -> None:
        """Record a skipped domain. No capture is written."""
        name = self.config.require_domain(domain)
        if name not in self.domains:
            raise SessionError(f"Domain {domain!r} is not in this cycle.")
        if name not in self._skipped:
            self._skipped.append(name)

    # -- completion -----------------------------------------------------

    def completion_report(self) -> dict:
        """Structured report: what was captured, where, what was skipped."""
        return {
            "domains_captured": sorted(self._captured),
            "paths": {d: r.path for d, r in sorted(self._captured.items())},
            "domains_skipped": list(self._skipped),
            "domains_untouched": [
                d for d in self.domains
                if d not in self._captured and d not in self._skipped
            ],
            "next_actions": ["continue", "deepen a domain", "distill", "exit"],
        }

    def render_report(self) -> str:
        """Human-readable completion report."""
        report = self.completion_report()
        lines = ["Interview complete.", ""]
        if report["domains_captured"]:
            lines.append("Captured:")
            for d in report["domains_captured"]:
                lines.append(f"  - {d}: {report['paths'][d]}")
        else:
            lines.append("Nothing captured.")
        if report["domains_skipped"]:
            lines.append("Skipped: " + ", ".join(report["domains_skipped"]))
        if report["domains_untouched"]:
            lines.append("Untouched: " + ", ".join(report["domains_untouched"]))
        lines.append("")
        lines.append(
            "Next: " + " / ".join(report["next_actions"]) + "."
        )
        return "\n".join(lines) + "\n"


__all__ = [
    "InterviewSession",
    "SessionError",
    "InterpretationError",
    "CaptureResult",
    "MemoryConfig",
]
