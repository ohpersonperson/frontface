# DRAFT PR — merge-sandbox → upstream/master (DO NOT MERGE without Ryan's word)

## What
6 harvest commits from the ff-rumen calibration (Oct 5), plus the sandbox
rectification merge. All 8 packages: 480 tests green, dist artifacts built.

## Commits
- `abd6981` memdate digest continuity + tz-aware timestamps; proofit severity/--strict; flashy checkpoint digest binding; pressit null-escape fix
- `02091cc` PARAM-MEMINQU-004: mandatory capture_mode
- `daff647` PARAM-FAIRIT-002: looks_category_only gate declines surfaced
- `f9b6aaf` PARAM-FAIRIT-001: mandatory claimed origin_type
- `e4935e9` PARAM-PROOFIT-002: sanctioned, auditable waiver
- `33e0708` PARAM-PRESSIT-003: evasion pre-scan + hard warning
- `d7b5c67` PARAM-PROOFIT-002 (repair): ledger waiver rule numbers + regression test

## Test results (2026-10-07, local)
- pressit: 56 passed
- proofit: 90 passed
- flashy: 49 passed (+5 subtests)
- memdate: 79 passed
- meminqu: 45 passed
- metacog: 41 passed (+5 subtests)
- fairit: 64 passed
- postmo: 56 passed
- **Total: 480 passed, 0 failed**

## Builds
All 8 packages built (sdist + wheel) in `<pkg>/dist/`. Versions still 1.0.0 —
bump + tag needed before PyPI publish (that's the release-spec decision).

## Blocked
`git push origin merge-sandbox` rejected: gh OAuth token lacks `workflow` scope
(branch touches `.github/workflows/publish.yml`). To unblock:
`gh auth refresh -s workflow` (Ryan runs this), then push + `gh pr create --draft`.

## NEEDS RYAN (not done)
- Merge approval
- Version bump + tag decision (1.0.1? 1.1.0?)
- PyPI publish
