# 61f255726e2e — bounding-box outline of every object

On a blank canvas, the canonical Racket rule draws the perimeter of each same-color 4-connected object's bounding box in that object's color. Bbox interiors become 0, so blob cells inside the box are erased.

Every canonical bbox has a side of 2, where the outline equals the filled box, so the four canonical pairs cannot separate this rule from "fill the bbox" or "keep the blob and add its outline". Sampler 3.0.0 places at least one hollow object (bbox 3x3 to 5x5) whose blob crosses the bbox interior in every grid. It adds 0–3 canonical-style thin objects (2xk) and, in some grids, a second hollow object that may be an empty-interior perimeter arc. Objects have distinct colors, exact bboxes and at least one background cell between bboxes. `grid_h` 7..14, `grid_w` 9..16, `n_hollow` 1..2 and `n_thin` 0..3 are exact overrides in every band and observable from pixels.

The canonical rule (hash `afb437709cc6`) is unchanged. Per-color and 8-connected readings of the rule remain indistinguishable on this manifold by construction (distinct colors, one component per color); see `notes.md`. Approval is derived by the catalog from current code and retained evidence; this summary is not approval.
