# Solve work log

I had not opened the canonical rule, any generator implementation, reference solution,
private label, prior solve explanation, or repair source before this solve.

## Revision 1 — enclosed-region flood fill

Observation: every color-2 cell lies inside a closed wall made of color 1.  The output
recolors the entire wall-bounded non-1 region containing that seed to color 3.  This
explains the 3x3 fill in examples 0 and 4, the two-cell fill in the small rectangle of
example 1, and the one-cell fills inside the nested 3x3 frames.  The larger annular
space in the nested examples is not recolored because it does not contain a seed.

Program: find 4-connected components after treating color 1 as an impassable wall.
For each component, record whether it touches the grid boundary and whether it contains
color 2.  Recolor the whole component to 3 exactly when it contains a seed and is
closed off from the boundary.  Preserve all color-1 walls and all unrelated cells.

Remaining uncertainty: the examples use rectangular walls, but the component rule is
more general.  I chose it because the outputs depend on enclosure rather than rectangle
size, seed count, or nesting depth.
