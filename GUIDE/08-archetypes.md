# 08 · Task archetypes — from task smell to plan

Look at the train pairs, match the smell, follow the plan. Each plan names
the idioms (04) and functions (02) to reach for. Most real tasks combine
two or three archetypes.

| # | Smell (what you see in the pairs) | Plan |
|---|-----------------------------------|------|
| 1 | Only colors change; geometry identical | `cellmap` with a `cond`/`casev` per value, or the `recolor` family. No objects needed. |
| 2 | Output = input with some cells filled/erased by a local condition | `cellmap` reading neighbors via `safe-at`, or compute the cell set first (`filter` over `grid-positions`) and `recolor-cells` once. |
| 3 | Discrete THINGS move / get selected / counted | `objects` (same-color), `objects-8`, or mask+objects for multicolor. Then `pick-max`/`filter`/sorts over `obj-*` accessors. |
| 4 | One special object among many (odd one out, biggest, most holes) | Score each object (`obj-size`, `topo-count-holes`, `sym-class` idiom) → `pick-max`/`find-first`. Output often `mask-of` or a crop (`subgrid` on its bbox). |
| 5 | Hollow rectangles acting as containers | `frame?` idiom. Interior = `subgrid` of bbox+1 margin. Keys/markers usually sit just outside a corner or above the top edge. |
| 6 | Things fall / slide / stack | Occupancy-mask gravity idiom: sort movers (which settles first?), `drop` fold with a `fits?` probe. For single cells `gravity` may suffice. |
| 7 | Broken symmetry to repair, or mirror-image completion | `detect-mirror-symmetry` / per-object symmetry via `normalize-cells` + `member`; paint missing cells from their mirror positions. For 4-fold: the dihedral partner formulas. |
| 8 | Same shape appears rotated/flipped elsewhere | `all-transforms` membership or `match-transform` for the index; the `spin` table when other data must transform by the same index. |
| 9 | Line/ray drawing from markers | `ray`/`walk` idiom, or `smear-color`; blockers checked per step. |
| 10 | Grid of panels separated by full lines | `row-uniform?`/`col-uniform?` separators → band `spans` → per-panel `subgrid`; compare/vote/copy panels (`equal?` on grids works). |
| 11 | A small tile repeats / fractal self-similarity | `detect-translational-period`, or find the one content block and `build-grid` with `modulo` indexing. |
| 12 | Legend or header row controls the behavior | Slice the header off (`subgrid` from row 1), decode it into parameters (counts via `count-if` on `(row g 0)`), then run the body archetype. |
| 13 | Output much smaller: a census / answer strip | Compute the statistic per object/band, emit with `build-grid` or a literal `(list (list ...))`. |
| 14 | Output much larger: scaled or gallery | `upscale`, or build panels and paste side by side with 1-gaps (gallery fold in 04's stamping idiom). |
| 15 | Two halves/panels combine cell-wise | Split at the separator, then `cellwise`/`grid-and`/`grid-or`/`grid-xor` or an explicit `build-grid` combining `(at a r c)` and `(at b r c)`. |
| 16 | Enclosed pockets matter (inside vs outside) | `find-0-regions` + border-touch filter, `topo-count-holes`, `fill-all-enclosed`, or boxed `connected-region` floods from the rim. |
| 17 | A template stamps at marker positions | Extract template (bbox `subgrid` or `mask-of`), find anchors, `stamp` fold with clipping; orientation/color per marker via a small dispatch table. |
| 18 | Path through a maze / connect points | an explicit BFS for shortest path (`bfs-path` is not a loaded primitive); the Kruskal/corridor pattern for connect-all; elbow walking (vseg/hseg) for routed pipes. |

## When nothing matches

1. Diff the pairs cell-by-cell (`grid-diff` mentally or via features): what
   EXACTLY changed? Where do the changed cells sit relative to objects?
2. Name the roles out loud; write the comment header first.
3. Solve ONE pair by hand as data (which cells, which colors); then find the
   computation that produces those cells; then check it on the other pairs.
4. Prefer the dumb-but-explicit plan (scan + filter + paint) over a clever
   one — brute force over a 30×30 grid is free.
