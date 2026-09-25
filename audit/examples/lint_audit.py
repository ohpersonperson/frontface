#!/usr/bin/env python3
"""Lint an audit draft against the five disciplines.

Usage:
    PYTHONPATH=src python3 examples/lint_audit.py --text draft.txt
    PYTHONPATH=src python3 examples/lint_audit.py --text draft.txt \
        --restatement restatement.txt

Every hit is a REVIEW item for the operator — the scan finds, the
operator decides. Exit code 0 always; this is a linter, not a gate.
"""

from __future__ import annotations

import argparse
import sys

from postmo import scan_text


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True, help="Audit draft to scan.")
    parser.add_argument("--restatement", default="",
                        help="The auditor's restatement (enables the D5 "
                             "softening comparison).")
    args = parser.parse_args()

    with open(args.text, encoding="utf-8") as f:
        text = f.read()
    restatement = ""
    if args.restatement:
        with open(args.restatement, encoding="utf-8") as f:
            restatement = f.read()

    report = scan_text(text, restatement=restatement)
    if report.clean():
        print("No mechanical flags. (Not a clean bill of health — "
              "see the discipline table for what stays human.)")
        return 0

    if report.subordinators:
        print(f"[D1] subordinating conjunctions: {', '.join(report.subordinators)}")
        print("     Held tensions must be parallel sentences, never 'X, but Y'.")
        print()
    for hit in report.verdict_words:
        print(f"[D2] permanent-label language: {hit.word}")
        print(f"     -> {hit.sentence}")
        print("     REVIEW: verdict word — the teller's word (their CLAIM) "
              "or the auditor's verdict?")
        print()
    for cand in report.correction_candidates:
        print("[D3] untyped correction candidate "
              f"(marker: {cand.marker!r}):")
        print(f"     -> {cand.sentence}")
        print("     Type as detail or core-claim, or drop it.")
        print()
    for flag in report.motive_flags:
        print(f"[D4] supplied motive ({flag.severity}):")
        print(f"     -> {flag.sentence}")
        if flag.severity == "flag":
            print("     No attribution marker — the teller didn't state this why.")
        else:
            print("     Marked as a guess — allowed, but it must stay marked.")
        print()
    for flag in report.softening_flags:
        print(f"[D5] softening [{flag.kind}]:")
        print(f"     {flag.detail}")
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
