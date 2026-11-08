# Solve notes

## Visible evidence
All three demonstrations preserve shape and every cell except one whole yellow
(4) connected component, which becomes green (3).  In each example the changed
component is the one whose bounding box has the smallest left column.  This is
not equivalent to choosing the topmost component: training examples 0 and 1
change a bottom component while yellow components occur at the top.

## Hypothesis
Find cardinally connected yellow components; rank them by minimum column
(left edge), breaking an otherwise irrelevant tie by minimum row; recolor the
selected component from 4 to 3 and preserve all other cells.

## Implementation
The solution performs an explicit four-neighbour flood fill and edits a deep
copy.  It does not assume a border location, fixed shape, fixed component count,
or fixed canvas size.

## Exposure declaration
I had already seen the task rule while reviewing the generator, so this is an
exposed post-repair solve, not a blind solve.  During this solve episode I used
only the prepared visible examples and did not consult the Racket authority,
generator source, reference solutions, or private labels.
