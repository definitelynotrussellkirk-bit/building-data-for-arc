# Solve work log

## Exposure declaration before solving
I had not opened task `37aaf7d1e52e`'s generator, Racket rule, notes, prior solves, or private labels. I only read the supplied visible `challenge.json` after `blind prepare`.

## Revision 1 — enclosed-background extraction

**Hypothesis.** Each nonzero drawing acts as a wall. The output erases the wall and copies its color only into zero cells completely enclosed by it. Evidence: the 3×3 rings leave one center pixel; the 4×4 rectangle leaves a 2×2 interior; the 3×5 outline leaves its two separated interior zero cells; the open color-7 shape in the last lesson produces nothing. Extra outward protrusions do not matter.

**Program.** Flood-fill zero cells reachable from the grid border as outside. Every remaining zero component is a hole. Color each hole using the most frequent nonzero 4-neighbor wall color, while returning zero everywhere else.

**Expected tests.** The first query should leave orange 7 at the ring center. The second should leave a 2×2 blue block inside the 4×4 loop despite the one-cell protrusion above it.

**Alternatives considered.** Bounding-box interiors fit most lessons but could incorrectly fill an open or concave drawing, so I rejected it in favor of topological enclosure. A per-object component flood-fill is unnecessary for the visible cases; global outside fill correctly supports multiple disjoint objects and holes.

**Remaining uncertainty.** A hole bounded by several colors is not shown. The implementation chooses the majority adjacent wall color deterministically; all visible enclosed regions have a single wall color.
