# 96fc9e1b827a — largest-object column histogram

Version `3.0.0`; canonical rule hash `0fb26a20e01c`.

A black-background grid contains exactly three separated monochrome objects in
distinct nonzero colors. Select the unique largest object by **cell count** and
replace it with a tight, top-justified cyan(8) histogram whose column heights are
the selected object's per-column cell counts.

The default four-sample schedule deliberately mixes:

1. a canonical-scale anchor using one of the three canonical target masks; and
2. three lawful counterexamples where the winner is right/bottom while a smaller
   left object is wider and has a larger bounding box.

This refutes the canonical-fitting shortcuts `leftmost_object`,
`largest_bbox_area`, and `widest_object`. Exact controls are available for
`grid_h`, `grid_w`, `target_shape`, `target_slot`, and `distractor_style`; unknown
or incorrectly typed controls fail loudly. The selected Racket authority was not
changed.

Kind: `per_puzzle`. Approval remains a catalog/maintainer decision derived from
current code and retained evidence.
