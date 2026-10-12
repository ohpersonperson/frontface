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

from postmo import Correction, render_correction_coverage, scan_text
from postmo.scans import CORRECTION_KINDS


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--text", required=True, help="Audit draft to scan.")
    parser.add_argument("--restatement", default="",
                        help="The auditor's restatement (enables the D5 "
                             "softening comparison).")
    parser.add_argument("--typed", default="",
                        help="File of operator-typed corrections, one per "
                             "line as 'kind: sentence text' (feeds the D3 "
                             "typing-coverage report).")
    args = parser.parse_args()

    with open(args.text, encoding="utf-8") as f:
        text = f.read()
    restatement = ""
    if args.restatement:
        with open(args.restatement, encoding="utf-8") as f:
            restatement = f.read()

    typed: list[Correction] = []
    if args.typed:
        with open(args.typed, encoding="utf-8") as f:
            for lineno, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                kind, sep, sentence = line.partition(":")
                kind, sentence = kind.strip(), sentence.strip()
                if not sep or kind not in CORRECTION_KINDS or not sentence:
                    print(f"warning: {args.typed}:{lineno}: skipping "
                          f"malformed typed-correction line: {line!r}",
                          file=sys.stderr)
                    continue
                typed.append(Correction(kind=kind, text=sentence))

    report = scan_text(text, restatement=restatement, typed=typed)
    print(render_correction_coverage(text, typed))
    print()
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
