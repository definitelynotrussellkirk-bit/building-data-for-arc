# Solve work log

Earlier exposure: none to this task's generator, rule, reference solution, private
labels, or prior solve notes. I read only `solve-blind/challenge.json` plus the
blank solve harness before writing the solution.

## Revision 1 — singleton components become maroon

Across all three visible pairs, every nonzero 4-connected component containing
one cell is recolored to 9, while every component with at least two same-colored
orthogonally adjacent cells is preserved. The decisive example is the first
training pair: color 6 occurs both as a horizontal two-cell component and as a
separate singleton; only the singleton changes. This rules out a simple
"recolor colors occurring once" explanation and points to object/component size.

I implemented same-color, four-neighbor flood fill and recolor components of size
one. I considered diagonal connectivity, but no visible pair requires it; ARC
object conventions and the explicitly adjacent dominoes make four-connectivity
the least-assumptive rule. I also considered recoloring every isolated nonzero
cell regardless of neighboring different colors; the implementation treats
objects by equal color, so a differently colored neighbor does not merge them.

Before implementation I ran a temporary visible-example regression against the
blank `solution.py`; it failed at `NotImplementedError`, as expected. After the
change I reran the same three visible examples. Remaining uncertainty is limited
to whether the hidden instance contains diagonal same-color contact and expects
8-connectivity; the training evidence favors the simpler four-connected reading.
