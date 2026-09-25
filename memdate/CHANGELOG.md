# Changelog — memdate (front-facing memdate-v2)

All notable changes. The package converts the `memdate-v2` skill
(Ryan's skill-suite, MIT) into front-facing, production-ready code.
This changelog doubles as the decoupling record: every entry names what
was changed and why.

## 1.0.0 — 2026-09-24

### What was built

- `memdate` Python package, stdlib-only (no third-party
  dependencies): `config`, `adapters`, `frontmatter`, `capture`,
  `distill`, `index`, `drop`.
- The CAPTURE/DISTILL/INDEX mechanism converted intact — the skill's
  core invariant (CAPTURE preserves, DISTILL interprets, never mix them)
  needed no translation. The isolation checks moved from prose
  checklists into code: capture has no edit code path (append-only by
  construction), distill checksums raw around every run and voids the
  run on any change, the index verify pass asserts no orphans.
- 72 offline unit tests, all passing — they prove the machinery, not
  just the prose.
- CLI (`examples/run_local.py`): `init`, `capture`, `distill`, `index`,
  `sweep`. Fully offline.
- 1 worked example a stranger can follow (two neutral domains, full
  cycle, actual file contents at each step).

### Decoupling decisions

1. **Renamed `memdate-v2` → `memdate`.** The old name told a
   stranger nothing; "ledger" names the append-only record at the
   system's heart.
2. **Domains are configuration, not identity.** The skill shipped
   Ryan's domains (`personal`, `fhk`, `tribunal`, `memory-system`,
   `misc`). The package ships neutral defaults (`personal`, `work`,
   `projects`, `reference`, `misc`) and takes the list from the
   constructor, JSON, or a small documented YAML subset. `fhk` and
   `tribunal` appear nowhere in the defaults — the tests assert their
   absence.
3. **Local filesystem is the default; Drive is an optional seam.** The
   skill's primary location was Ryan's `!Memory` Drive folder. The core
   talks only to a `StorageAdapter`; `LocalFilesystemAdapter` works out
   of the box. `GoogleDriveAdapter` documents the seven-method interface
   and raises `DriveNotConfigured` with implementation pointers on any
   call — it fails loudly instead of pretending to work. A subclass can
   wire the real Drive API or the `gws` CLI.
4. **Evidence taxonomy reconciled with the IFS package.** memdate never
   tagged evidence, so there was no competing taxonomy to merge — but
   the artifacts sit at defined tiers of the converted IFS ten-tier
   system, and the mapping is now explicit in the README (raw →
   OBSERVATION/CLAIM, distilled → INFERENCE, open questions → UNKNOWN).
   No code dependency between the packages: the table is the contract,
   so the two can't silently fork.
5. **DROP ingestion layer kept and hardened.** The skill's storage
   layout included a DROP ingestion layer; it's now `drop.py` with
   explicit routing rules — unroutable or synthesis-smelling files go to
   QUARANTINE with a reason file, never silently captured or deleted.
6. **No model backend shipped.** Unlike the IFS and metacog conversions,
   this package never calls a model: capture/distill/index govern text
   the caller supplies. The distill protocol (what a model should do)
   is documented; the enforcement (what the library guarantees) is code.

### Lossy in translation — honest notes

- **The interpretation scan is heuristic.** "In summary" usually means
  synthesis, but a raw quote could contain the phrase ("he said 'in
  summary, we're fine'"). The marker list is configurable and `force`
  records the bypass visibly — the failure mode is a false refusal, not
  silent corruption, and the bypass leaves a paper trail.
- **Entity extraction is caller-declared, not automatic.** The index
  builds Entities→Domains from frontmatter `entities` lists, not by NLP
  over the body text. Automatic extraction would need a model or an NLP
  library; declared entities keep the package stdlib-only and make the
  index deterministic. The cost: the distiller (human or model) must
  name entities.
- **The YAML config parser is a strict subset**, documented as such.
  Full YAML would need PyYAML; the subset covers what a memory config
  needs (scalars and lists). JSON is supported for anything fancier.
- **`! ` divergence notes rely on distiller honesty.** The library can
  detect that raw changed (checksum) but can't detect that distilled
  *misrepresents* raw — that judgment stays with the distiller. The
  `! ` convention gives them a place to flag it.
