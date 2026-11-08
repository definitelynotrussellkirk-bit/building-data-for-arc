# Solve work log

## Exposure declaration before solving

I had not opened the task's generator, Racket rule, reference solution, private labels,
or earlier explanations. I used only `solve-blind/challenge.json` and local Python
experiments over its visible examples.

## Revision 1 — horizontal component gravity

The first and last columns are solid rails of two colors, with color 7 as the
background. Interior objects use the same two rail colors. Comparing the four
visible training pairs showed that each 4-connected object moves horizontally
toward the rail of its own color while preserving its shape.

A simple “place each object at the farthest non-overlapping final position” was
almost sufficient, but a concave packing case in training example 4 distinguishes
true stepwise motion: the right-moving singleton on row 6 cannot jump through a
gap beyond the L-shaped piece. Therefore pieces settle nearest-edge first and each
piece advances one column at a time until the next step would collide with the
rail-connected component or an already-settled same-color piece. Opposite colors
are processed independently, which is required by training example 1 where the
left-moving object passes the original location of a right-moving object.

I implemented that rule generically: detect the dominant background and the two
rail colors, find 4-connected components, keep rail-connected components fixed,
clear all movable components, then pack left-color components left and right-color
components right in distance-to-rail order. A local comparison against all four
visible outputs matched every cell. Remaining uncertainty is limited to tie cases
where two components have the same distance to a rail; the examples do not require
another tie-break beyond top-to-bottom order.
