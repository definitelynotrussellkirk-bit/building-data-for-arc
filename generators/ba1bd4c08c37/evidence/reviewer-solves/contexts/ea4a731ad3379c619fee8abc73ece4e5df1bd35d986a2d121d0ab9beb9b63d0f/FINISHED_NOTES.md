# Solve work log

## Prior exposure declaration

Before this solve I had already reviewed the assigned generator and its authority,
so earlier rule exposure is **yes**. During this solve I did not reopen the
Racket rule, generator implementation, reference solutions, private labels, or
older solution explanations. The reasoning below uses only the visible examples
printed by `solve prepare`.

## Revision 1 — nonzero bounding-box top-left half

All five demonstrations contain one foreground arrangement that is symmetric
across both axes. Its nonzero bounding box is even-sized. The output dimensions
are exactly half the bounding-box height and half its width, and the output
matches the raw top-left portion of that box, including internal zero cells.

Visible checks:

- Example 0 has an 8×8 foreground box at rows 2..9, columns 2..9; output is its
  rows 2..5 and columns 2..5.
- Example 3 has a 6×10 foreground box at rows 0..5, columns 6..15; output is the
  3×5 raw top-left crop.
- Example 4 has a 10×6 box at rows 6..15, columns 0..5; output is the 5×3 raw
  top-left crop.

This distinguishes the rule from cropping the whole canvas, returning a fixed
4×4 patch, or choosing another quadrant. I implemented: find the min/max row and
column containing any nonzero value, compute floor-halves of that box, and return
the top-left half-height by half-width crop. The visible family always has even
box dimensions; floor division keeps the implementation shape-safe if not.

Predicted query shapes are 3×3 and 4×4. Remaining uncertainty is only masked
query correctness, which the visible-only checker intentionally withholds.
