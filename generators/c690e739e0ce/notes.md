# Working notes: c690e739e0ce

## Current decision

Retain the canonical default byte-for-byte as `(rule! flip-lr)` and propose one
nearby episode-fixed setting, `reflection_scope=minority_rows`.

- **A:** count every non-background color and derive the unique globally
  least-frequent color.
- **Intermediate:** the complete row mask containing that color.
- **B:** reverse exactly those full rows left-to-right.

The setting changes only reflection scope, preserving the source task's core
row-mirroring operation. Inputs are sampled independently of the private setting
and therefore match exactly across settings.

## Base repair

Canonical pairs and ordinary/boundary generation matched horizontal reflection.
The base validator did accept strings such as `"012"` as rows because
`_coerce_grid` iterated and digit-coerced them. It now requires literal row lists;
focused regressions also cover boolean cells and ragged rows.

## Constructive two-demo lesson

The minimum is deliberately crossed rather than two same-scale random scenes.

- Demo 0 is 10x12, has 2 selected rows, selector/decoy global counts 3/4,
  mixed left/right placement, and the only top-left selector coincidence.
- Demo 1 is 14x16, has 9 selected rows, selector/decoy counts 18/19, no
  top-left coincidence, and a pure-dense unselected guard row.
- Dense colors are omitted from at least one marked row and remain more frequent
  than the decoy. Every row is asymmetric.

This construction repaired concrete minimum-lesson holes found during review:
left-half-only markers, edge-only markers, exactly-one/odd marker counts, a fixed
selector count, fixed frequency thresholds, and first/last-N selected-row caps.

## Bounded self-review

`workspace/parametric/adversarial_probe.py` compares compact row-mask signatures
and materializes only genuinely non-mask wrong operations. The retained audit
covers 64 seeds x demo counts 2/3/6 x 2 settings = 384 episodes, all ten selector
colors, 402 distinct selected-row masks, fixed colors, frequency ranks,
exact/threshold frequencies 1..40, first/last selected rows 1..8, parity/halves,
position and row-statistic shortcuts, and partial/wrong intermediates.

Final retained result: no profile failures, no wrong rule fitting all demos while
changing a query, and no non-declared distribution-equivalent survivor. Stale
programs, duplicate inputs, wrong labels/counts, booleans, forged certificates,
and private/future-query leakage were also checked. This is finite evidence, not
a universal uniqueness proof.

## Limits and status

The alternative requires a unique global minority color; the constructive sampler
enforces this grammar. Four distinct controller-side queries are retained and
shown one at a time, including a substantive 30x30 scene. Protected-Racket
execution, source inventory, author qualification, and a replayable causal witness
are required evidence; owner exact-source acceptance and training admission remain
separate and pending. Approval flags must not be edited here.
