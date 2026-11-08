# Solve notes

This is a human work log based only on `solve/challenge.json`. I had earlier
exposure to the task family while repairing the generator, so this is not a
blind solve; I did not reopen the generator, Racket source, reference solution,
or private labels during this episode.

## Visible-example hypothesis

Each input is divided into monochrome panels by columns that are zero in every
row. The output size equals the number of panels. Diagonal entries are always
5. An off-diagonal pair is 2 exactly when the two occupied-cell shapes match
after cropping and allowing rotations or mirror reflections; otherwise it is 0.
Color and placement inside the common three-row canvas are irrelevant.

Evidence from the visible examples:

- Example 1 marks all three pairs equivalent despite visibly different
  orientations.
- Example 2 marks only panels 1 and 2 equivalent, while the third has a
  different shape.
- Example 3 marks only panels 2 and 3 equivalent.
- Example 4 contains three distinct shapes and therefore only the diagonal.
- Example 5 again makes all three panels equivalent.

## Implementation

Split on full-height zero columns, crop each panel to occupied cells, binarize,
enumerate four rotations of both the original and a left-right reflection, and
use the lexicographically smallest binary grid as the shape signature. Build
the pairwise relation matrix from those signatures.
