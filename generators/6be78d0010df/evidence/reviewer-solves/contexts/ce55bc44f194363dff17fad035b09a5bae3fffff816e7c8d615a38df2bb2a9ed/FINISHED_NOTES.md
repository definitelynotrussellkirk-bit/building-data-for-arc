# Solve work log

## Prior exposure

This is not a blind solve. Before `solve prepare` I repaired this task's generator and read the canonical rule while validating it. During this solve I did **not** reopen the generator, Racket rule, reference solutions, private labels, or earlier solution explanations; I used only the displayed examples and this solve workspace.

## Revision 1 — cropped panel analogy

The inputs contain two full-height color-1 divider columns, making three equal panels. The nonzero object in the first panel and the object in the second panel have the same cropped mask even when their absolute row/column offsets differ. Cellwise correspondence between those two crops defines a consistent color substitution. The output is the third panel's nonzero bounding-box crop with that substitution applied, preserving zeros and shape.

Visible checks:

- Example 0: the first crop is `[5,5,3,3]`, the second is `[6,6,9,9]`, so `5→6` and `3→9`; applying that to the third crop gives the shown 3×2 output.
- Example 1 establishes a three-color map despite different panel placements.
- Examples 2 and 3 confirm that interior zeros survive and output dimensions equal the third object's tight crop, not the full panel.

Implementation: locate the two divider columns, split panels, crop each to nonzero bounds, verify A/B masks and mapping consistency, then recolor cropped C. Remaining uncertainty is low because all four visible examples exercise shifted placement, multiple colors, and internal zeros.
