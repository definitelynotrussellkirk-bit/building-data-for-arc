# Allocation-quality probe — ticket-b861724e7953d89f

Status: completed, bounded static evidence.

The ticket-seeded draw over the actual 162-record normal pool reproduced:
`7c7f1f574a18`, `9c26c4b2c305`, `5553241d87bf`. All are approved and carry
dataset weight 1.0, but retained evidence maturity differs: the first two expose
focused curriculum/rival tooling and strong accepted-repair evidence; the third
is reviewed-safe but has thinner task-local lesson/rival/schedule evidence and a
more complex separator/template grammar. None ships a public bounded parametric
four-query prototype. The draw contains only training/augmented sources; it does
not cover ARC-GEN or RE-ARC.

Estimated alternative, without changing the 10% evaluation focus or admission
and training-weight rules: allocate the remaining review budget 50% to approved
reviewed-safe originals missing a bounded parametric/four-query artifact, 30% to
records with ambiguity/grammar/dedup evidence debt, and 20% to source-family and
discovery coverage including eligible ARC-GEN/RE-ARC records.

Bounded test: 60 assignments per arm, capped at 30 reviewer minutes and 2,000
Racket evaluations each. Stop after 20 per arm if accepted lessons/hour improves
by under 10% or post-intake rejection rises by over 5 percentage points;
otherwise complete 60 and adopt only when the lower 95% bootstrap bound on the
accepted-lessons/hour difference is positive.

All quality/cost comparisons are estimates from retained static evidence; no
fresh Racket, model, corpus-wide rejection or deduplication job was run.
Machine-readable evidence: `result.json`. Reusable probe: `allocation_probe.py`.
