# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, notes, reference solution,
private labels, or prior solve records. I used only `solve-blind/challenge.json`
and local Python checks against its four visible training pairs.

## Revision 1 — red-anchored shortest path

**Observation.** Every grid has exactly one blue cell (`1`) and one red cell
(`2`). The output preserves them and adds green (`3`) cells forming a shortest
8-neighbour path between them. It is not a Bresenham/straight-line raster: in
training pair 2, for example, the greens contain a long horizontal segment.

**Ordering hypothesis.** Read the path from red toward blue. If both row and
column differ, take one diagonal step first. Then consume the entire excess on
the dominant axis (the absolute row/column-distance difference). Finally take
the remaining diagonal steps to blue. Paint every intermediate cell green and
leave both endpoints unchanged. This ordering exactly explains all four pairs,
including the asymmetry that places the straight segment next to the red side.

**Probe.** I loaded `challenge.json`, ran this implementation on each visible
training input, and compared the full output grid. Expected query consequences:

- query 1: green at `(4,4)` and `(5,4)` (zero-indexed);
- query 2: green at `(11,6)`, `(10,6)`, `(9,6)`, `(8,6)`, `(7,5)`, `(6,4)`.

**Alternatives rejected.** A Euclidean/Bresenham line and an arbitrary shortest
path both fit the vague idea of "connect the markers" but not the exact visible
cell placements. Starting the excess-axis segment from the blue side also fails
the asymmetric examples.

**Remaining uncertainty.** No visible pair is axis-aligned. The implementation
extends the same shortest-path rule naturally by filling a straight segment
between the markers in that case.
