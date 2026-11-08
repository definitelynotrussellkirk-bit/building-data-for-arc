# Solve work log

## Exposure

Before this solve I had not opened this task's generator, Racket rule, reference
solution, private query labels, prior solution notes, or any generator assigned
for repair. I used only the visible examples produced by `blind prepare` and my
own local calculations.

## Hypothesis

Each nonzero 4-connected monochrome object keeps its color and bounding-box
anchor, but is reflected across the anti-diagonal of that bounding box. In local
coordinates for a box of height `h` and width `w`, an occupied cell `(r, c)` moves
to `(w - 1 - c, h - 1 - r)`. All shown boxes are square, so their occupied cells
remain inside the same box.

Evidence from the visible examples:

- The three-cell `[[1, 1], [1, 0]]` object becomes
  `[[0, 1], [1, 1]]`, exactly its anti-diagonal reflection.
- The six-cell object `[[0,0,1],[1,1,1],[1,1,0]]` becomes
  `[[0,1,1],[1,1,0],[1,1,0]]` under the same transform.
- Applying the transform independently to every object reproduces all objects in
  all three training pairs, including multiple disconnected objects of one color.

Alternatives considered were a rotation, a main-diagonal transpose, and a
shape-dependent canonical orientation. A single anti-diagonal reflection explains
all examples while those alternatives fail at least one asymmetric object.

## Implementation and probe

The solver finds 4-connected components separately by color, clears their old
cells, and paints each component's anti-diagonal reflection from the untouched
input. Processing from an immutable copy avoids one transformed object affecting
component discovery for another. A local test compares `solve()` with all three
visible training outputs.

Remaining uncertainty: no visible example has a non-square bounding box or a
collision between transformed objects. The coordinate formula handles rectangular
boxes by swapping local height and width while retaining the top-left anchor, but
the task may intentionally restrict objects to square boxes.
