# public_eval_de809cff — rectangle restoration and hole clusters

## Design and implementation plan
Reconstruct the solid rectangle layers from long same-color runs, infer their
occlusion order from overlap votes, and erase non-rectangular color noise. A
missing cell is an original zero whose reconstructed layer is nonzero. The
canonical rule marks every such cell cyan and paints its eight-neighborhood in
the other rectangle color, even when that halo extends outside a rectangle.
All centers are painted last, so adjacent holes retain both centers.

The alternative `hole_scope=largest_cluster` selects all maximum-area
four-connected missing-cell clusters before painting. Other missing cells are
restored to their inferred rectangle colors. This retains reconstruction and
adds an input-dependent global selection; it is not a change in input sampling.

- [x] Test original labels, repair semantics, and independent cluster selection.
- [x] Build self-contained sampler and an identical task-local native resource.
- [x] Execute canonical and alternate Racket programs; attack finite rivals.
- [x] Test independent 2–6 demos/1–4 queries and private shuffled four-query bank.
- [x] Freeze source, run public authoring preflight, replay causal witness and exports.

Scope: only this home; no catalog, canonical ledger or approval edits. Existing
packet is an isolated extracted workspace with no Git metadata. A full native
owner admission remains separate from authoring verification. Planned self-review
is by the author (no independent reviewer/subagent), with retained finite evidence.

## Verified current result
60 tests pass. All 2 train labels and the 30x30 original test match protected
Racket. Audit covers 12 episodes, 92 label claims, 40 distinct protected
executions, and 132 named rival checks. The first audit found a harmful
ignore-boundary shortcut; the second demonstration now puts a maximum cluster
on the canvas boundary. First demonstrations also distinguish four- from
eight-connected hole clusters. The fixed audit has no harmful survivors.
Preflight, 16 shuffled public views, and a 21-cell causal counterexample pass.
Owner registration, native qualification and acceptance remain pending.

## Admitted grammar and limits
Exactly two nonzero/noncyan rectangle colors; well-supported straight bounds;
recoverable acyclic occlusion; sparse isolated color noise; no contradictory
overlap vote. The 18–30 sampler constructs 2–3 layers and checks recovery against
its pristine construction. Original dimensions down to 20 are also validated.
Finite audits do not establish uniqueness against arbitrary programs.
