# Visible-only solve work log

I had prior exposure to this rule family during the assigned generator review, so
this is an exposed post-repair solve, not a blind solve. During this solve phase I
used only the visible examples printed by `solve_episode.py prepare`; I did not
reopen the generator, Racket rule, prior solutions, or private labels.

## Hypothesis

The grid is copied except for two perimeter cells per non-6/non-7 interior
object. Each object is a single-colored cross. Its center is the cell with four
same-colored orthogonal neighbors. Count the contiguous/object cells above,
below, left, and right of that center. The unique longest arm defines a facing
perimeter endpoint along the same row or column. Clear that facing endpoint to
0 and paint the opposite endpoint with the object's color.

The examples distinguish this from “paint the nearest side”: for example, a
long arm can face a farther side, but the paint still goes to the side opposite
the arm. Components are grouped by color and 4-connectivity so differently
colored touching crosses remain distinct.

## Implementation plan

Copy the input; flood-fill each interior color other than 6/7; choose the cell
with the greatest count of same-component orthogonal neighbors as center; count
component cells on each axial ray; apply the two perimeter edits. Preserve all
interior cells and all unrelated frame cells.
