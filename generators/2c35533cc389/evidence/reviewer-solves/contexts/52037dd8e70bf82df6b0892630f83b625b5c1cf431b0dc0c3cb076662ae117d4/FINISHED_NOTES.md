# Visible-example solve log

This is a human work log, not a captured model trace. I had earlier rule exposure
from the generator review, so the final declaration must be `earlier-exposure
yes`. During this solve phase I used only the displayed examples and did not
reopen the generator, Racket rule, reference solution, or private labels.

## Hypothesis

Every red cell (`2`) in the input remains in place and paints a blue cell (`1`)
one column to its right when that destination is in bounds. Sources must be read
from the original input: training example 2 contains adjacent reds, and its
output shows the left red overwriting the right red with blue while the original
right red still paints one step farther right. A right-edge red paints nothing,
as visible in training example 1.

## Implementation

Copy the input, collect every original red coordinate, then paint color `1` at
`(row, column + 1)` for each in-bounds source. No shape or palette change is
needed. One revision was sufficient because the three examples explicitly cover
ordinary writes, right-edge clipping, and occupied-destination/source-order
semantics.
