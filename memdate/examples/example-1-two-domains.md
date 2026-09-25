# Worked example: two domains, end to end

A complete CAPTURE → DISTILL → INDEX cycle using the neutral default
domains `work` and `personal`. Everything below runs against a scratch
directory — nothing here touches your real files.

*The field is constructed for teaching — it shows the mechanism's shape,
not real findings.*

## 1. Configure and lay out the store

```python
from memdate import MemoryConfig, ensure_layout, default_adapter

cfg = MemoryConfig(root="/tmp/demo-memory")   # neutral defaults: personal, work, ...
ensure_layout(cfg)                             # root + DROP/ + per-domain dirs
```

Layout after init:

```
/tmp/demo-memory/
├── DROP/NEW/  DROP/PROCESSED/  DROP/PENDING/  DROP/QUARANTINE/
├── personal/
└── work/
```

## 2. CAPTURE — raw records, no interpretation

```python
from memdate import capture

store = default_adapter("/tmp/demo-memory")
capture(cfg, "work", "Acme Corp emailed: contract renews March 1, same terms.",
        source="email", adapter=store)
capture(cfg, "work", "Priya said the Q1 budget is frozen until the audit closes.",
        source="standup", adapter=store)
capture(cfg, "personal", "Dentist appointment moved to Thursday 9am.",
        source="phone", adapter=store)
capture(cfg, "personal", "Priya mentioned she might switch teams in March.",
        source="call", adapter=store)
```

`work/raw.md` now holds two timestamped entries, verbatim. Try to slip
in synthesis and the library refuses:

```python
>>> capture(cfg, "work", "In summary, the Acme deal is basically safe.",
...         adapter=store)
InterpretationError: Entry looks like interpretation, not capture —
markers found: in summary. Rewrite as raw record, or pass force=True
to record the bypass explicitly.
```

## 3. DISTILL — consolidate, with provenance

The caller supplies the synthesis (a person, or a model following the
distill protocol). The library stamps it and proves raw wasn't touched:

```python
from memdate import distill

distill(cfg, "work",
        "Acme Corp contract renews March 1 on current terms.\n"
        "Q1 budget frozen pending audit close.\n"
        "? Whether the freeze affects the Acme renewal paperwork.",
        entities=["Acme Corp", "Priya"],
        entity_notes={"Acme Corp": "client, renews March 1"},
        informs=["personal"],
        open_questions=["Does the budget freeze delay the Acme paperwork?"],
        lifecycle="ITERATIVE",
        adapter=store)

distill(cfg, "personal",
        "Dentist Thursday 9am.\n"
        "Priya may switch teams in March.",
        entities=["Priya"],
        entity_notes={"Priya": "colleague, possible team switch"},
        adapter=store)
```

Note the `? ` line in the work distillation — an uncertainty flag the
index will pick up as a hot zone. And `informs=["personal"]`: the work
domain's material informs the personal domain (the Priya thread crosses
both).

Each `distilled.md` carries frontmatter:

```
---
artifact: memdate-distilled
domain: work
date: 2026-09-24
protocol: memdate/1.0.0
lifecycle: ITERATIVE
entities:
  - Acme Corp
  - Priya
entity_notes:
  Acme Corp: client, renews March 1
informs:
  - personal
open_questions:
  - Does the budget freeze delay the Acme paperwork?
---
```

## 4. INDEX — regenerate the connective tissue

Two domains were distilled, so the index regenerates (a single-domain
distill would skip with a recorded reason):

```python
from memdate import regenerate_index

result = regenerate_index(cfg, touched=["work", "personal"], adapter=store)
print(result.reason)   # Regenerated from 2 distilled domains.
```

`INDEX-cross-domain.md`:

```
---
artifact: memdate-cross-domain-index
date: 2026-09-24
protocol: memdate/1.0.0
lifecycle: ITERATIVE
---

# Cross-domain index

## Entities -> Domains

- **Priya**: personal, work — colleague, possible team switch

## Dependencies

- work informs: personal

## Open Questions

- Does the budget freeze delay the Acme paperwork? (from work)

## Hot Zones

- [work] uncertainty: Whether the freeze affects the Acme renewal paperwork.
```

"Acme Corp" doesn't appear under Entities → Domains — it's referenced
in only one domain, and the index is cross-domain tissue, not a census.
The entity notes for Priya differ across the two distillations
("colleague, possible team switch" vs. none recorded in work), but they
don't conflict, so no tension flag fires. If work had said "Priya:
reliable on deadlines" and personal had said "Priya: misses deadlines",
that contradiction would land in Hot Zones as `[tension]`.

## 5. The invariant, in one line

`work/raw.md` is byte-identical to before the distill — the library
checksums it around every distill run and voids the run if anything
changed it. Raw is authoritative; distilled was corrected toward raw,
never the reverse.
