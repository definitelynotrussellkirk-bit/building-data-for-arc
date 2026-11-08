# 54a83e6bbc20

On background 7, match each cyan (8) left jigsaw piece to the uniquely colored
right piece that completes a solid 3×5 rectangle. Preserve the cyan pieces'
vertical positions and draw the completed rectangles at the left.

Kind: `per_puzzle`. Current implementation version: `4.0.0` (imported: `3.0.0`).

The sampler now uses all 64 three-row cut vectors and all 2/6/24 permutations
for 2/3/4-piece scenes. Equal-area anchors defeat area-only matching; row-collision
anchors make omitted rows relevant. Three consecutive default demonstrations
cover the declared query-changing rivals. Four width-tie geometry sets are
excluded to preserve the unchanged selected Racket authority.

Use `workspace/run_review.py` for source-bound tests and shortcut/oracle probes.
The exact 32-value scene axis is manually tested because the shared automatic
enum probe is capped at sixteen; all 96 scene × shape combinations are covered.
Approval remains catalog-derived; this source change does not auto-approve itself.
