"""The Quality Gate: the launch checklist that guards VERIFYING -> DONE.

There is no partial credit. Every box checked or the task is not done —
status stays IN PROGRESS, not "mostly done."
"""

from __future__ import annotations

GATE_ITEMS = (
    "Everything requested exists",
    "Everything builds/holds together logically",
    "Nothing obvious is missing",
    "No placeholder implementations remain",
    "No TODOs remain",
    "No incomplete sections remain",
    "No artificial stopping points remain",
)


class GateError(ValueError):
    """An unknown gate item was referenced."""


class QualityGate:
    """Seven boxes. Check them all or stay in VERIFYING."""

    def __init__(self) -> None:
        self._boxes: dict[str, bool] = {item: False for item in GATE_ITEMS}

    def check(self, item: str) -> None:
        if item not in self._boxes:
            raise GateError(f"Unknown gate item: {item!r}")
        self._boxes[item] = True

    def uncheck(self, item: str) -> None:
        if item not in self._boxes:
            raise GateError(f"Unknown gate item: {item!r}")
        self._boxes[item] = False

    def all_checked(self) -> bool:
        return all(self._boxes.values())

    def missing(self) -> list[str]:
        return [item for item, checked in self._boxes.items() if not checked]

    def check_all(self) -> None:
        for item in self._boxes:
            self._boxes[item] = True

    def status(self) -> str:
        return "DONE" if self.all_checked() else "IN PROGRESS"
