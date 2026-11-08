# Blind solve notes — d2534264df36

## Exposure

I did not inspect this task's generator, canonical rule, reference solution, private labels, or prior task-specific notes. Before the draw I had opened packet-level guidance (`WELCOME.md`, `ARC-DESIGN.md`, and repository overview material), so this is not a perfectly procedure-clean start even though those files did not reveal this task's rule. I record the task-rule exposure itself as `no` and reference consultation as `no`.

## Hypothesis

The non-zero cells occupy every other row and column, forming a smaller logical square lattice. The input is a compact diagonal staircase beside one physical corner. In corner-relative coordinates:

- `(k, k)` gives the corner color of concentric square layer `k`.
- `(k, k+1)` and `(k+1, k)` give the color extended along that layer's horizontal and vertical edges.
- The output completes all four sides/corners of every encoded layer, leaving all other cells zero.

The first and third demonstrations show that the encoded corner may be top-left or bottom-left, so the program scores all four orientations. The correct orientation keeps every clue within one cell of the main diagonal and minimizes distance from the candidate corner.

## Probe

I downsampled the first demonstration to its 10×10 active lattice. Its output decomposes into rings:

- layer 0: corner color 2, no edge color;
- layer 1: corner 6, edge 4;
- layer 2: corner 8, no edge;
- layer 3: corner 7, edge 9.

The second and third demonstrations have the same representation, including a bottom-left encoding in the third example. I implemented this directly, with separate horizontal/vertical edge colors if they ever differ and a symmetric fallback when only one redundant edge clue is present.
