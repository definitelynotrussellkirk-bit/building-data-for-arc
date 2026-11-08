# ffcd7510821d — Marker-Count Rotation

Count maroon (9) cells **only on row 0**, clear only those cells, crop all remaining
nonzero content, and rotate the whole crop clockwise by the count modulo four.
Racket authority is unchanged; normalized rule hash `77da9e97370c`. Black is background.
Off-row 9s are outside this generator's domain, not globally erased by the rule.

Version **3.0.0** generates 7–14 by 8–14 grids, a blank separator row, and 1–4
separated connected nonrectangular blobs in distinct colors 1–8. All four rotations
of the **complete content crop** must be different. Nonrectangular alone is not
sufficient: a plus is symmetric.

Four fixed-seed consecutive default examples cover marker counts 1, 2, 3, and 4;
there are two single-object anchors and two multi-object scenes. Every difficulty
retains canonical-scale anchors. Explicit controls are grid_h, grid_w, n_markers
(0–4), n_blobs, and palette_kind (warm/cool/varied), honored over their full domains
regardless of difficulty. Unknown keys and removed v2 aliases now raise.

The task workspace contains Racket-backed census/audit tools and a handoff.
The local lesson hook provides finite rotation-table and named-rival checks, not
proof against arbitrary programs. Explicit overrides or nonconsecutive sampling
can remove default teaching coverage. Approval remains derived by the catalog
from current source and independently retained evidence, not from this summary.
