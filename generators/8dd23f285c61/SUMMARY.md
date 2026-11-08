# 8dd23f285c61 — Shoot Rays Until the Walls

Generator version: `3.0.0`. Canonical rule hash: `346b3beb0ce3`.

Inputs are 7..16 by 9..16 grids over colors `0` (background), `2`
(emitter), and `5` (wall). Each grid contains 2..5 emitters and 1..4
four-connected, mutually disconnected wall components. Wall morphology includes
one- or two-cell blockers as well as longer horizontal/vertical barriers.

For every color-2 emitter, the output changes the emitter to color `8` and casts
color-8 rays in all four orthogonal directions. Each ray stops before the first
color-5 cell or at the grid edge. Walls remain color `5`; all untouched cells
remain unchanged.

Every ordinary draw contains a tiny wall directly in one emitter's ray with
open space behind it. This explicitly refutes the canonical-compatible shortcut
“ignore one- and two-cell walls.” Exact override axes are `grid_h`, `grid_w`,
`n_seeds`, and `n_wall_components`.
