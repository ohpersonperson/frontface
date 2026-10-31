# Frontface cold-start tutorial (Spine 5 draft, 2026-10-28)

Zero-assumption walkthrough for a stranger with Python 3.10+ and git. Built only from material verified in Spines 1–4 (corrected test counts, the patched root test loop, and the friction fixes). Nothing here needs an account, a key, or an install — except the last section, which says so up front.

## 0. What you need

- Python 3.10 or newer (`python3 --version`).
- git.
- Every package is stdlib-only and fully offline, except the two engine tools in section 9, which need a model backend. One install is still needed: the root test loop in section 1 uses pytest, which is not in the standard library:

```bash
python3 -m pip install pytest
```

## 1. Get it and prove it

```bash
git clone https://github.com/ohpersonperson/frontface.git
cd frontface
```

Run the whole suite first. This is the patched loop from the root README: seven packages in the loop, meminqu as its own step because it imports memdate's core.

```bash
for d in ifs metacog flashy memdate probe-forge audit proofit; do
  PYTHONPATH="$d/src" python3 -m pytest "$d/tests/" -q
done
PYTHONPATH="meminqu/src:memdate/src" python3 -m pytest meminqu/tests/ -q
```

Expect eight green summaries, one per package, in this order: 64, 55 (+5 subtests), 52 (+5 subtests), 79, 87, 86, 121, 51 passed — 595 in total. If any step is not green, stop — the rest of this tutorial assumes a green tree.

## 2. The map (read this before you type `cd`)

Run the sections in order: each section's `cd ../<dir>` assumes you are still in the previous section's directory. If you jump in mid-tutorial, `cd` to the named directory from the repo root instead.

Package names and directory names differ for three tools. The docs use directory names, so do the same:

| Tool | Directory | Job in one line |
|---|---|---|
| pressit | `ifs` | Pressure-tests a claim until what's load-bearing is left standing |
| proofit | `proofit` | Fail-closed linter for runbooks: shape, not truth |
| flashy | `flashy` | Finishing discipline: checkpoints, gates, no dropped threads |
| memdate | `memdate` | File-based memory: capture raw, distill separately |
| meminqu | `meminqu` | Interviews a memdate store, captures answers raw |
| metacog | `metacog` | Audits whether confidence is earned |
| fairit | `probe-forge` | Catches responsibility-obfuscation in how something is said |
| postmo | `audit` | Holds a messy multi-person situation without resolving it early |

`cd pressit`, `cd fairit`, and `cd postmo` do not exist. Use `ifs`, `probe-forge`, and `audit`.

## 3. proofit: see a PASS before you see a REJECTED

Lint the known-good file first, so you know what passing looks like:

```bash
cd proofit
PYTHONPATH=src python3 -m proofit lint examples/fixed-runbook.md
# (a blank line, then) PASS: no violations — the runbook is locked down.
```

Now print the blank template and lint it. Expect REJECTED — the template's placeholders (like `[observable success condition]`) are not observable checks yet. That is the linter working, not failing:

```bash
PYTHONPATH=src python3 -m proofit template > my-runbook.md
PYTHONPATH=src python3 -m proofit lint my-runbook.md
# Violations listed (first is RULE 6: verification not objectively checkable),
# ending in a REJECTED summary.
```

Two rules that surprise newcomers: proofit checks a runbook's **shape, not its truth** — a fully-specified unwise workflow passes, a wise but sloppy one doesn't. And warnings (rules R1, R5, R8, R13) pass in default mode and only fail under `--strict`; structural errors always fail.

## 4. flashy: prove the machinery, then watch it finish

```bash
cd ../flashy
PYTHONPATH=src python3 -m unittest discover -s tests   # 52 offline tests
python3 examples/demo_session.py                        # ends: "The user has the finished thing, not a starting point."
```

The `PYTHONPATH=src` on the test line matters — without it the tests fail with `No module named 'flashy'`. The demo needs no path because it sets its own up. The demo ends with the line "The user has the finished thing, not a starting point."

## 5. fairit: one full cycle, no model needed

```bash
cd ../probe-forge
PYTHONPATH=src python3 examples/run_cycle.py
```

This runs ground → probe → brief on a sample text and ends with handoff seeds: phrases where language erases the actor exactly where accountability would attach.

## 6. memdate: a memory store in four commands, one shell

The `export` must stay in the same shell for all four commands:

```bash
cd ../memdate
export PYTHONPATH=src
python3 examples/run_local.py --root /tmp/memo init
python3 examples/run_local.py --root /tmp/memo capture \
  --domain work --text "Acme Corp emailed: contract renews March 1." --source email
```

Capture preserves raw records without interpretation. If you capture something that reads like interpretation ("In summary, the deal is safe"), expect an `InterpretationError` telling you to rewrite it as a raw record or pass `force=True` to record the bypass explicitly. Distill separately, from a file holding your consolidated synthesis — never by editing raw records in place.

## 7. meminqu: the interviewer needs memdate on the path

```bash
cd ../meminqu
PYTHONPATH=../memdate/src:src python3 -m unittest discover -s tests   # 51 offline tests
PYTHONPATH=../memdate/src:src python3 examples/demo_interview.py
```

The double path is the whole trick: meminqu deliberately imports memdate's shared core instead of duplicating it, so a bare `PYTHONPATH=src` fails. The demo leaves its store under `/tmp/interview-demo-*` and says so when it ends.

## 8. postmo: lint an audit draft

```bash
cd ../audit
PYTHONPATH=src python3 -m unittest discover -s tests   # 86 offline tests
PYTHONPATH=src python3 examples/lint_audit.py --text examples/bad-draft.txt \
  --restatement examples/bad-restatement.txt
```

Expect flags like softening and ambivalence-resolved. Postmo holds tensions as parallel sentences; it does not pick a side for you.

## 9. pressit and metacog last: these two need a model

Both are engines that run on a model following a protocol prompt. Their tests run offline (pressit passes with no path at all; metacog needs `PYTHONPATH=src`), but a real run needs a backend, and the docs' only line is "a model to run the engine on." Concretely:

- **pressit:** install and start Ollama and pass `--ollama <model>`, or export `OPENROUTER_MODEL` and `OPENROUTER_API_KEY`. With neither, `run_local.py` stops with `No backend selected.` — that message is the whole story, not a bug.
- **metacog:** with no backend it uses a stub. A conclusion under 40 words fails the stub's steelman check on purpose (`RUN FAILED: countermodel failed the steelman check (weak): too-short`). Use at least 40 words, with named premises, evidence, or mechanism. A RUN FAILED line from that check is the check working, not a crash.

```bash
cd ../ifs
python3 -m unittest discover -s tests   # 64 offline tests, no path needed
cd ../metacog
PYTHONPATH=src python3 -m unittest discover -s tests   # 55 offline tests
```

## 10. The ledger (documented, not part of the walkthrough)

Six tools (pressit, proofit, flashy, metacog, fairit, postmo) keep a local append-only ledger at `~/.frontface/<tool>/ledger.jsonl`: one record per run — timestamps, counts, verdicts, confidence deltas. It never stores your input text, only a SHA-256 digest of it. Opt out with `FRONTFACE_NO_LEDGER=1`, or move it with `FRONTFACE_LEDGER_DIR=/path`.

## Troubleshooting

| You see | It means | Do this |
|---|---|---|
| `ModuleNotFoundError: No module named 'flashy'` (or `'metacog'`) | The test line needs the package on the path | Add `PYTHONPATH=src` before the test command |
| `No backend selected.` | pressit has no model to run on | Install/start Ollama (`--ollama <model>`) or export `OPENROUTER_MODEL` + `OPENROUTER_API_KEY` |
| `RUN FAILED: ... too-short: N words (minimum 40)` | metacog's stub steelman check, working as designed | Use at least 40 words with named premises/evidence |
| `REJECTED` (first violation RULE 6) on a blank template | Placeholders aren't observable checks | Lint `examples/fixed-runbook.md` first to see a PASS, then fill the template in |
| `cd pressit` / `cd fairit` / `cd postmo` fails | Those are package names, not directories | Use `ifs`, `probe-forge`, `audit` |
| `InterpretationError` on a memdate capture | The entry reads like interpretation, not capture | Rewrite as a raw record, or pass `force=True` to record the bypass |
| meminqu import errors | memdate isn't on the path | Use `PYTHONPATH=../memdate/src:src` |

Done. You have now run six tools end to end, tested all eight, seen a PASS and a REJECTED, and hit every first-hour wall on purpose instead of by accident. (pressit and metacog were tested only — their real runs need a model backend, section 9.)
