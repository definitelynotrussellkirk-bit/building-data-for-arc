# Exposed post-repair solve work log

This is a human work log. I had already inspected the assigned generator and
canonical rule during the repair, so this is not blind. During this solve phase I
used only the visible presentation produced by `solve prepare`; I did not reopen
the generator, Racket source, private labels, previous solve explanations, or
reference outputs.

## Hypothesis from visible demonstrations

Each input contains several nonzero four-connected same-color objects. The
outputs are exact bounding-box crops of objects that are left-right symmetric as
raw pixel rectangles. Width-one vertical bars should not count as evidence of
left-right symmetry because they are vacuous. When more than one qualifying
object exists, the demonstrations select the one with the most occupied cells,
not necessarily the largest bounding-box area or earliest/lowest object.

## Implementation

1. Enumerate same-color four-connected components in row-major discovery order.
2. Crop each component's bounding rectangle from the original grid.
3. Keep width > 1 crops whose full rows equal their reversals.
4. Return the crop of the eligible component with greatest occupied-cell count.

The implementation intentionally evaluates symmetry on the complete raw crop,
including zeros and other colors inside the bounding rectangle, because that is
what the displayed outputs suggest.
