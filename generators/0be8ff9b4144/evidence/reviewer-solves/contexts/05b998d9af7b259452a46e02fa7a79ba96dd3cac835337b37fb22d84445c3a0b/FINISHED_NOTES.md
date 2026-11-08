# Post-repair visible-example solve notes

## Hypothesis

Treat the first row and first column as headers, excluding their shared corner.
A body row is selected exactly when its first cell is green (`3`). A body column
is selected exactly when its top cell is red (`2`). Replace every selected
row/column intersection with gray (`5`) and preserve every other cell.

## Evidence from the visible examples

- Example 0 has two `3` row headers and three `2` column headers, producing the
  six-cell Cartesian product.
- Example 1 is the key negative example: a top-header `3`, a left-header `2`,
  unrelated body `8`s, and a non-`8` corner do not activate anything. Only
  top-header `2` and left-header `3` matter.
- Example 2 has a nonzero background and pre-existing body content. The same
  header test applies; selected intersections are overwritten with `5`, while
  non-intersection content remains.

One direct implementation covers all three demonstrations, so I stopped after
its first visible check. I had already seen the task's rule while repairing the
generator, so this is not a blind solve; I did not consult the reference source
during this solve episode.
