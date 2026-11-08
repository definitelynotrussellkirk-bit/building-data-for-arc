# Solve work log

## Prior exposure

This is not a blind solve. Before `solve prepare` I had inspected and repaired the
selected generator and had seen the intended Racket rule. During this solve I did
not reopen the generator, Racket source, reference solutions, private labels, or
prior solution explanations. The implementation below is a reconstruction checked
against only the three visible examples.

## Revision 1 — original-grid extent comparison

The examples show monochrome bands with zero holes. A hole causes a full row or
column segment of its surrounding band color to become zero. The direction is not
simply perpendicular to band orientation: in training example 1 the two vertically
aligned holes in color 8 produce a column for the upper hole and a row for the lower
hole.

Hypothesis:

1. For each original zero, select the first in-bounds nonzero neighbor in the order
   up, down, left, right. This gives the hole's latent band color.
2. On the original input, count cells equal to that color **or zero** across the
   hole's complete row and complete column.
3. If the row count is at least the column count, erase the matching color/zero
   cells in that column; otherwise erase them in that row.
4. Accumulate all erasures in the output, but keep every neighbor/count decision
   bound to the original input so earlier erasures do not change later choices.

Checks by inspection:

- Training 1, hole `(5,3)`: its color-8 row support ties/exceeds its column support,
  so column 3 is erased. Hole `(6,3)` has shorter row support than column support,
  so row 6 is erased.
- Training 2, holes in the narrow color-6 and color-5 bands prefer columns, while
  isolated holes in broad horizontal color-2 rows prefer rows. The visible output
  matches that split.
- Including all zeros in an extent is necessary for the multi-hole rows; counting
  only the selected color would change some decisions.

I implemented this directly in `solution.py`. Remaining uncertainty is limited to
neighbor-order edge cases not separately exposed by the three visible examples;
the displayed examples are consistent with the stated up/down/left/right order.
