# Solve work log

## Prior exposure

This is an exposed post-repair solve. Before preparation I had inspected the assigned generator and canonical rule while reviewing it, so earlier rule exposure is **yes**. During this solve I did not reopen the generator, Racket rule, reference solutions, private labels, or earlier solution explanations. I used only the newly prepared visible examples and the checker.

## Revision 1 — reflected terrain copied in the sparse color

The modal color is background. Of the two other colors, the more frequent color forms a terrain/profile plus a sparse straight reference line; the less frequent color forms a second sparse line with the same row or column coordinates.

Visible examples suggest:

1. Identify whether the sparse-color markers share one row or one column.
2. Find the parallel source-color line whose occupied coordinates exactly match the sparse marker coordinates.
3. Take source-color cells on the side of the sparse line opposite that parallel line.
4. Translate/reflect those cells so their distance from the sparse line is reproduced beyond the parallel line, and paint the copied profile with the sparse color.
5. Preserve the input everywhere else.

For horizontal lines the copied row is `target_row + marker_row - source_row`; for vertical lines the analogous column formula applies. This explains all three visible examples, including examples where the terrain is above or below the marker line. Query 0 exercises the vertical orientation and query 1 uses color 0 as the sparse paint color, so the implementation infers roles by frequency rather than assuming fixed color IDs.

Remaining uncertainty: the code assumes exactly two non-background role colors and a unique parallel line with an exact marker-coordinate match, which is supported by every visible example.
