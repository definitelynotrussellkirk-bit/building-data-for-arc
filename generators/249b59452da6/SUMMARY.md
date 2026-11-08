# 249b59452da6 — Complete red diagonals

Version **3.0.1**. Canonical rule pin: `e42ab715e8c9`.

Inspect every 2x2 window in the original input. Exactly two red cells (2) must
occupy opposite corners and both other corners must be zero. Paint those two
zeros green (3), considering both diagonal orientations and all eligible windows
simultaneously. Preserve everything else, including nonred diagonals, occupied
corners, red bars, and isolated distractors.

## Input distribution

Ordinary draws have dimensions 9..18, 3..5 distinct input colors, and 2..8 eligible
windows. A five-profile schedule places four canonical dimension/palette tuples
alongside one broader draw. Every ordinary grid carries counterexamples to all
12 declared rivals, including nine shortcuts that fit all five canonical pairs.
Smaller 2/3-window scenes maintain canonical object-count support; larger scenes
combine separated chains, tailed zigzags, and extra pairs. The rule is local, so
connected red components and overlapping windows are intentional.

Exact controls: integer `grid_h`/`grid_w` in 4..18, `n_pairs` in 1..10, and
`palette_size` in 2..5. `n_pairs` is the observed number of eligible original
2x2 windows, including overlaps; `palette_size` includes background zero and
red. Invalid controls fail explicitly. A valid joint tuple either materializes
exactly or raises `IncompatibleAxes` with the actual axes. This refusal means
unsupported by the bounded placement family, not mathematically impossible.

Constrained controls (small grids, palette two, counts one/nine/ten) use a compact
checkerboard-subset family and do not promise the full ordinary teaching
curriculum. All outputs remain the responsibility of the canonical Racket rule.
The sampler constructs inputs and never uses rival outputs to filter them.

## Review evidence and tools

The final 12-stage battery passes. The official census retained 300 lessons and
1,200 unique inputs/query rotations with no declared-rival ambiguity. The task
probe checks all 9,000 joint tuples, malformed controls, deterministic defaults,
consecutive lesson windows, and optional Racket parity. See `workspace/README.md`
for commands and limitations, and the packet's `REVIEW.md` for final acceptance
evidence. Passing checks do not change catalog training approval.
