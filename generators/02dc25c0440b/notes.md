# Working notes: 02dc25c0440b

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/02dc25c0440b/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-26 parametric build decision

The ordinary generator and exact selected canonical Racket source required no source repair. The new episode-fixed parameter is `right_label`: `source_color` preserves the canonical mirror rule byte-for-byte; `visible_size` first builds that mirror, then recolors each right-side component by the number of cells remaining visible after clipping. In the first-round sampler, every scene included a five-cell source object clipped to a connected four-cell mirror, plus separate distractors. That established the sequential dependency but left a size shortcut, repaired in round two below.

The first-round wrong-intermediate counterfactual labeled the clipped mirror with source size 5 instead of visible size 4 and changed the selected protected-Racket output. The authoring preflight passed both settings at seeds 0 and 17 (32 protected-Racket evaluations), the causal witness replayed, and the 16 one-query public projections verified. These are reviewer authoring results only; owner source review, native qualification/acceptance, and any training admission remain pending.


## 2026-10-26 adversarial round 2

A minimum-two-demo adversarial scan found that the original clipped construction
always mapped source size 5 to visible size 4. Both a fixed clipped label of 4
and a “source size minus one” rule therefore fit the lessons. A regression test
captured both shortcuts and failed on the old sampler. The repaired sampler now
uses one-cell loss in the first demo and multi-cell loss in the second, with
source/visible pairs drawn from 3→2, 4→3, 6→4, 6→5, and 7→4.

Fresh evidence records 14 passing task tests, a 128-seed matched-input sweep with
visible sizes 2–5 and clipping losses 1–3, 72 additional protected-Racket parity
evaluations, four authoring-preflight jobs with 32 protected-Racket evaluations,
causal-witness replay, 16 public projections, and first-turn invariance checks.
Scope remains finite; owner acceptance and training admission remain pending.
