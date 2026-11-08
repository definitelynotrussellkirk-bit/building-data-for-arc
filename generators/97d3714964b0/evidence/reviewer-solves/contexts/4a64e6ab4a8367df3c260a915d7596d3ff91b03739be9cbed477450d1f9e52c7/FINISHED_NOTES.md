# Visible-only solve notes

## Hypothesis from the three demonstrations

Treat each 4-connected orange (7) object independently. The output preserves the
canvas and object cells, replacing an object by yellow (4) when its bounding box
contains an empty interior cell (a hollow frame), and by red (2) when its bounding
box is completely occupied (a solid rectangle).

The strongest visible contrast is that equal-size objects can receive different
colors: in training example 1 the 3x3 hollow frame becomes 4 while the 3x3 solid
block becomes 2. This rules out size, position, and object-count shortcuts.

## Implementation

Find 4-connected color-7 components with a flood fill. For each component, inspect
strictly interior cells of its bounding box. Recolor all component cells to 4 if
any such position remains background 0; otherwise recolor them to 2. Preserve all
other cells. I did not consult any rule source, generator source, reference
solution, or private labels during this solve episode.
