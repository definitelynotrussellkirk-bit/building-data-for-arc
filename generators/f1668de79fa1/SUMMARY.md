# f1668de79fa1

Normalize the connected color-2 template to its tight bounding box, reflect it
left/right, and place its bounding-box top-left at the single color-1 marker.
Paint the surviving cells cyan (8) on a fresh zero grid. Cells outside the
canvas are clipped; the anchor never moves inward.

Version `2.0.1` generates 4..9-cell connected templates on 6..18 by 8..22
canvases. Symmetric templates and partially clipped stamps are lawful.
The input roles remain literal colors 0, 1 and 2; output ink remains 8.
The unchanged canonical Racket authority is pinned to `6fbd99546842`.

Exact controls: `grid_h`, `grid_w`, `template_cells`, and
`marker_mode=full|clipped`, with pixel-derived observations.
Unknown, retired inert, and malformed controls raise `ValueError`.

Default sampling cycles through core, wide, and clipped profiles, with a
seed-dependent phase. Unoverridden core examples have five vertically asymmetric
cells and a full stamp, refuting the five-cell conditional-rotation shortcut.
Full wide examples distinguish all D4 alternatives,
edge-column swapping, and boundary-only mirroring. Clipped examples
distinguish inward fitting. Five demonstrations plus one query support
leave-one-out rotations of six consecutive accepted pairs.
Explicit controls can disable these default curriculum guarantees while
remaining exact and lawful.

Kind: `per_puzzle`. Previous selected version: `1.4.0`.
Approval is derived by the catalog from current code and retained evidence.

The 2.0.1 collision merge retains the earlier accepted sampler and adds the
conditional rival/witness from `review-5f5dffd562b3002e`. Its new source was checked
with 205 focused task tests; the returned candidate's full-battery and solve
results retain their original source identity. See `notes.md` and the exact
source-bound machine receipt in `evidence/maintainer-merge-review-5f5dffd562b3002e.json`.
