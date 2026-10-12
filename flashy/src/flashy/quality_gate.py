"""The Quality Gate: the launch checklist that guards VERIFYING -> DONE.

There is no partial credit. Every box checked or the task is not done —
status stays IN PROGRESS, not "mostly done."

Trust contract (read this before trusting a "DONE")
-------------------------------------------------
The Quality Gate is a SELF-CERTIFICATION checklist, not a verification
record. It records the *operator's declaration* that each box holds —
nothing more. It holds no evidence, no timestamps, no identities, and no
audit trail; it cannot tell you who checked a box, when, or on what basis.

Consequences of that contract:

* ``check(item)`` records "the operator declares this box holds" — not
  "this box was independently verified to hold."
* ``check_all()`` is the speech act "I certify all of these." It is
  legitimate — and it is a declaration, not a proof of inspection.
  Calling it without having actually examined each item is a false
  certification, and the gate cannot detect the difference.
* ``status()`` returning ``"DONE"`` means every box was declared, never
  that a third party attested to anything.

The gate enforces *completeness of the declaration* — every box must be
checked. It does not, and cannot, enforce *truthfulness of what is
declared*. Do not mistake a checked gate for evidence.
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
    """Seven boxes. Check them all or stay in VERIFYING.

    Trust contract: this is a self-certification checklist. The gate
    records operator declarations — "I certify this box holds" — not
    evidence-backed verification and not third-party attestation. It can
    tell you every box is checked; it cannot tell you anyone inspected
    anything, nor who declared what, when, or on what basis.
    """

    def __init__(self) -> None:
        self._boxes: dict[str, bool] = {item: False for item in GATE_ITEMS}

    def check(self, item: str) -> None:
        """Record the operator's declaration that *item* holds.

        This is self-certification, not an inspection record: the gate
        stores that the box was declared checked, with no evidence, no
        timestamp, and no identity attached.
        """
        if item not in self._boxes:
            raise GateError(f"Unknown gate item: {item!r}")
        self._boxes[item] = True

    def uncheck(self, item: str) -> None:
        """Withdraw the recorded declaration for *item*."""
        if item not in self._boxes:
            raise GateError(f"Unknown gate item: {item!r}")
        self._boxes[item] = False

    def all_checked(self) -> bool:
        """True iff every box carries a checked declaration."""
        return all(self._boxes.values())

    def missing(self) -> list[str]:
        """Boxes with no checked declaration recorded."""
        return [item for item, checked in self._boxes.items() if not checked]

    def check_all(self) -> None:
        """Declare all seven boxes checked in one call.

        The speech act is: "I certify all of these." It is legitimate —
        and it records the operator's declaration, not proof of
        inspection. The gate treats this exactly like seven individual
        ``check()`` calls: a declaration with no evidence behind it.
        Calling this without having actually examined each item is a
        false certification the gate cannot detect.
        """
        for item in self._boxes:
            self._boxes[item] = True

    def status(self) -> str:
        """Return "DONE" iff every box carries a checked declaration.

        "DONE" means the operator declared completion — every box
        certified. It never means a third party attested to anything or
        that any evidence was reviewed.
        """
        return "DONE" if self.all_checked() else "IN PROGRESS"
