# Solve work log

This is the required post-repair visible-only solve. I had already read the
assigned generator and canonical authority while performing the repair, so this
is **not blind** and earlier rule exposure is `yes`. After `solve_episode.py
prepare` I used only `solve/challenge.json`; I did not reopen or consult the
Racket rule, generator implementation, private labels, reference solutions, or
prior solution explanations during this solve.

## Revision 1

Across all four visible demonstrations, each nonzero same-color 4-connected
component is replaced independently by the outline of its axis-aligned bounding
box on a fresh zero canvas. Missing bbox-edge cells are added in the component's
color, while source cells strictly inside the box disappear. The fourth example
contains two disconnected color-2 components and shows that equal colors are not
merged into one global box.

The implementation therefore finds same-color 4-connected components with BFS,
computes each component's row/column extrema, and paints only the corresponding
rectangle border into a new zero grid. The visible query inputs include both a
canonical small scene and a larger four-component scene, so the same component-
wise routine applies without a shape-size lookup. Remaining uncertainty is only
about domains absent from the visible lesson, such as overlapping bbox borders;
the displayed examples have disjoint boxes.
