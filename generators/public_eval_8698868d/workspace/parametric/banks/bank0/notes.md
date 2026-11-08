# Working notes: public_eval_8698868d

## 2026-10-25 reviewer-ready public creation

All authoring stages passed. Status is
`authoring_preflight_not_owner_qualification`; owner registration, source review,
native qualification and acceptance remain pending. Training is not admitted.
The immutable parent record binds public task `8698868d`.

### Rule and dependency

Infer the modal background. The colorblind four-connected foreground component
with the unique largest bounding-box area is the board. Detached monochrome
framed patterns have side n; board panels have side n+2. Match them by counts of
enclosed four-connected background regions, including zero. Rebuild panels in
their base colors and inset selected patterns with a one-cell margin. Pattern
ink keeps its color; pattern background becomes panel color, repairing clue
marks. Crop to the board. Hole area, color and location do not select the match.

`pattern_orientation="as_observed"` is canonical; `clockwise90` rotates each
matched pattern before insertion. A derives the count-based assignment; B selects
shape/color and renders from it. The causal intervention changes assignments
while keeping B byte-identical. Root reference.rkt and adjacent canonical.rkt
are identical; normalized rule hash is `6fd48cdc010b`. Replacing unavailable
`make-grid` with `grid-from-fn` fixed the initial protected runtime error; the
failed receipt remains. No supplied-grid or answer lookup is used.

### Construction and teaching

Support is 2..6 demos and 1..4 queries, ordinarily three and four. Preflight and
the teaching audit use the minimum two; `qualification_demos: 3` deliberately
selects three for a later owner check. Cores include asymmetric masks, zero
through five holes, unequal areas, four/eight-connectivity foils, connected
clues, source-order decoys, reused colors including foreground zero, and clue
cells requiring restoration beneath pattern holes.

Ten fixed profiles vary side 4..6, board lattice, counts and source layout. The
30x30 profiles contain 543 and 402 foreground cells. No retries are used. Labels
are recomputed after palette/global-D4 augmentation, keeping clockwise correct
after reflection. Independent streams preserve matched inputs across settings;
shuffle the full query bank before selecting a shorter prefix.

### Completed evidence

Paths below are under `checks/public_eval_8698868d/`.

- Focused tests: 118 passed (41 native, 77 audit). `sampler-v1.json`: 96/96 requests.
- `teaching-v1/private/audit.json`: 43 labels (three official, 40 generated),
  108 fits on seeds 0/17, 104 refutations and four intended-only survivors;
  all 16 query scores agree. Fits use only two demos before queries. The ledger
  records 275 requests, 211 protected evaluations and 64 cache hits, with no errors.
- `preflight/preflight.json`, `preflight/execution.json` and
  `preflight/original-pairs.json`: passed on seeds 17/43, both settings, minimum
  two demos/four queries, and both official training labels plus the test gold.
- `causal-observations.json`: four protected measurements. `causal/witness.json`
  and `causal/replay.json`: two cases constructed and replayed with an unchanged
  renderer; status `reviewer_replayed`.
- `preview-verify.json`: four episodes and 16 single-query views verified.
  Combined `checks/first-turn/` privacy checks passed 8 first turns, 32 views,
  48 hidden-field invariance checks and 8 positive controls.

### Limits and owner action

The validator requires framed objects, unique count matches, a unique modal
background and a unique largest board rectangle on exact ARC grids up to 30x30.
The sampler covers a structured subset. Finite labels, seeds, rivals and replay
do not prove universal identifiability, full-domain coverage, algorithmic depth
or learning gains. Private rule and query evidence stays controller-side.

The owner must verify parent linkage, register exact source/provenance, accept
its source review, then run native qualification and fresh acceptance. Retain the
failed iteration and exact-source receipts with the handoff.
