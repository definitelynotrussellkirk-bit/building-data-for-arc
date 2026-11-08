# Working notes: 44690b1b635f

## Current rule and authority

Wall color 8 blocks traversal. Of the two other marker colors, the color that
occurs once is the BFS origin and the other supplies the odd-distance color.
Four-neighbor BFS crosses markers and zero cells; reachable zeros are colored by
distance parity while walls, markers, and unreachable zeros are preserved.
The canonical Racket rule is unchanged and remains pinned by `RULE_HASH 72a0e00e932b`.

## Reversal: fixed geometry only → fixed anchors plus procedural topology

Version 3.0.0 exposed three exact public masks and 13 fixed generalized masks.
The retained audit showed that color-normalizing those masks leaves only 42
role layouts across all bands, allowing a template lookup to predict the
sampled distribution without learning maze traversal. The labels were correct;
the defect was finite geometry support.

Version 3.1.0 preserves every fixed profile and adds `procedural_maze`. It builds
a deterministic depth-first spanning tree on an odd-cell lattice, with a wall
perimeter and exactly one opened connector per tree edge. A source-side
recognizer accepts only connected, acyclic lattice mazes with one singleton and
three arm markers. This makes malformed grids, extra cycles, disconnected
mazes, and even/even holes fail validation rather than broadening the grammar
silently.

Local evidence in `checks/recovery/diversity-census.json` reports 64/64 unique
wall topologies for 64 forced draws in each band. In 800 ordinary draws per
band, 47 procedural draws yielded 47 unique procedural topologies; the complete
distribution had 59 normalized wall topologies and 548 unique exact inputs.
The three public anchors still appeared 151/800 times per band.

## Decisions and limits

- Procedural randomness uses only the keyed `GenCtx` RNG; global `random` state
  remains unchanged and repeated calls return fresh equal grids.
- The selected canonical rule and production parameter surface remain
  unchanged except for the new observable `scene_profile=procedural_maze`.
- Proposed `neighbor_mode` and parity `phase` variants live only under
  `workspace/parametric/`; acceptance of this generator must not approve them.
- The recovery environment lacked the original packet's Racket runtime and
  official check/package tools after a workspace reset. Local Python tests and
  hashes are complete, but Racket-backed labels, full battery, two random audits,
  post-repair visible solve, and official package replay remain open.
