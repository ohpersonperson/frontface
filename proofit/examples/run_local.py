#!/usr/bin/env python3
"""Demo: lint the broken draft (rejected), then the fixed draft (passes).

Run from the proofit directory:
    PYTHONPATH=src python3 examples/run_local.py
"""
import subprocess
import sys

BROKEN = "examples/broken-runbook.md"
FIXED = "examples/fixed-runbook.md"


def lint(path):
    r = subprocess.run(
        [sys.executable, "-m", "proofit", "lint", path],
        capture_output=True, text=True,
    )
    return r.returncode, r.stdout


def main():
    code, out = lint(BROKEN)
    print(f"--- {BROKEN} -> exit {code} ---")
    print(out.strip().splitlines()[-1])
    code, out = lint(FIXED)
    print(f"--- {FIXED} -> exit {code} ---")
    print(out.strip())


if __name__ == "__main__":
    main()
