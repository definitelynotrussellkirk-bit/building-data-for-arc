# fc999420d3aa

A zero-background grid contains one or two completable partial pluses. A target
is a nonzero center with exactly three same-color cardinal neighbors and one
zero cardinal neighbor. The unchanged canonical rule fills that zero with the
center color, simultaneously for every target, and preserves every other cell.
Generated target colors are distinct.

Version `3.0.0` exposes only three exact controls: `grid_h` (5..18), `grid_w`
(5..20), and `n_motifs` (1..2). A four-profile schedule includes canonical
height/width/palette anchors plus three decisive profiles with non-downward
missing arms, multiple targets, and isolated two-arm decoys. Every consecutive
three-example window therefore refutes the declared `downward_only`,
`first_target_only`, and `complete_two_or_more` rivals; this remains a finite
rival claim rather than universal identification.

The canonical authority is unchanged and pinned by `RULE_HASH=75975e426e4b`.
Task-local regression tests and a reusable quick probe live under `tests/` and
`workspace/`. Approval remains catalog/maintainer-derived; passing checks does
not itself admit training data.
