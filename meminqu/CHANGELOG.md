# Changelog — meminqu

## 1.0.0 — 2026-09-24

Front-facing conversion of the `meminqu-memory-interrogation` skill
(Ryan's skill-suite, MIT). Package name `meminqu`,
distribution name `meminqu`.

### Decoupling record

- **Renamed** `meminqu-memory-interrogation` → `meminqu`.
  The old name was opaque; the mechanism is an interviewer.
- **Domains are configuration, inherited, never re-declared.** The
  skill's fixed list (`personal`, `fhk`, `tribunal`, `memory-system`,
  `misc`) is gone. The session reads domains from the memdate
  `MemoryConfig` — the same single source of truth the memory store
  itself uses. A practitioner who wants `fhk` back adds it to their
  own config; the package ships nothing Ryan-specific.
- **"IFS, FHK reading" follow-up note dropped.** The skill mentioned
  post-capture analysis as a possible next step. The package does
  capture only; analysis is out of scope by design, not by omission.
- **Heading format defers to memdate.** The skill's `##
  YYYY-MM-DD` day-heading became the library's per-entry timestamp
  heading; the inquiry marker and register list ride in the entry
  body. Documented in README ("Where the formats meet").
- **The seven registers kept verbatim** — names, stances, rotation
  rule. They were already plain language; they are the skill's
  mechanism, not its decoration. Made into data so callers can extend
  the set without forking the code.
- **No model, no network.** The session is record-keeping machinery
  (state, formatting, capture calls, completion report). The live
  Q&A stays with the operator — the package is explicit about that
  boundary.

### What's new in code (had no code before)

- `plan_cycle`: deterministic register rotation (consecutive domains
  differ, full cycle covers all registers).
- `format_entry`: verbatim-preservation contract with tests.
- `InterviewSession`: domain walk, skip, explicit reassignment,
  completion report — all wired to memdate's capture.
- 36 offline tests (`unittest`), all green.
