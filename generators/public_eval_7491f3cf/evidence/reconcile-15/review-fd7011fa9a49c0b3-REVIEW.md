# Review fd7011fa9a49c0b3

Both assigned public-evaluation homes now contain full reviewer-ready authoring
prototypes. Neither is owner-registered, natively qualified, accepted, or
admitted to training; those remain separate owner gates.

## `public_eval_36a08778`

The canonical rule propagates magenta top-edge rays downward. At the first red
cell, it recovers the entire contiguous horizontal segment, paints a cap one
cell beyond each endpoint while preserving unrelated red cells, and continues
from every in-bounds endpoint column. The episode-fixed alternative retains only
the nearest endpoint, with left ties. The source reproduces six official train
pairs and two private-gold test pairs. A seed sweep exposed and repaired a
teaching-search defect at seed 119: rejected candidate demonstrations now advance
to the next bounded attempt instead of aborting generation.

## `public_eval_7491f3cf`

The canonical rule identifies the largest 8-connected guide wall and isolated
marker in panel one, floods the marker-side four-neighbor region, then composes
panels two and three into panel four. Panel two supplies the marked side and has
foreground priority on guide-wall cells. The alternative swaps panel roles. The
source reproduces four official train pairs and the private-gold test pair.

## Retained evidence

- Protected public-authoring preflights for both families, including exact
  original-pair replay, four generated jobs per family, source inventories, and
  program hashes.
- 37 and 33 changed-target tests, plus 11 reusable evidence-tool tests.
- 240 adapter-boundary requests per family across every declared count/setting
  combination for seeds 0, 17, and 43.
- 136 protected-Racket evaluations of explicit rival programs; no rival fit all
  demonstrations and then disagreed on a query.
- 32 one-query public exports and 32 hidden-field byte-invariance checks.
- Source-bound causal witnesses: replacing full segment recovery changed 48
  cells; replacing the flooded region with the marker cell changed 4 cells.

## Limits and next action

The adversarial sets and seed sweeps are finite, and the causal interpretation
is authored metadata backed by protected output replay rather than a universal
proof. An author self-review was performed because this harness has no enabled
reviewer subagent. The owner must reconcile any overlapping submission, register
exact source/provenance, accept the source review, and run unchanged-source
native qualification and fresh acceptance for both families.
