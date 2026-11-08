# Blind solve notes — d2f386d0e071

## Visible pattern

Each training output is the input union its left-right mirror image. The mirror
axis is the vertical center of the grid: between columns 3 and 4 for width 8,
through column 3 for width 7, between columns 4 and 5 for width 10, and through
column 4 for width 9.

Concrete checks:

- Train 0, width 8: `(0,1)=4` gains `(0,6)=4`; `(0,3)=2` gains `(0,4)=2`.
- Train 1, width 7: `(1,0)=9` gains `(1,6)=9`; center-column `(0,3)=4` stays single.
- Train 2, width 10: `(4,0)=6` gains `(4,9)=6`; `(1,2)=8` gains `(1,7)=8`.
- Train 3, width 9: `(4,1)=8` gains `(4,7)=8`; `(4,3)=7` gains `(4,5)=7`.

## Hypothesis

For every nonzero input cell `(r,c)`, also color `(r, W-1-c)` with the same
color. Preserve all original cells. No visible example contains a conflicting
pair of different nonzero colors, so the implementation fills only blank mirror
positions rather than inventing a conflict policy.

## Predicted query behavior

- Query 0, width 8: add mirrors at columns 7, 4, 4, 7, 7, and 6 for the six
  colored cells, with center-paired cells handled once.
- Query 1, width 7: add mirrors at columns 5, 4, 5, 3, 6, and 3 as applicable;
  cells on center column 3 remain unchanged.

No task-specific generator, rule, reference output, notes, or audit record was
consulted.
