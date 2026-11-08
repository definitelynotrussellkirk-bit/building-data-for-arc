# Solve work log

## Exposure declaration

Before this solve I had already reviewed the task's generator, so earlier rule
exposure is **yes**. During this solve I did **not** consult the Racket rule,
generator implementation, reference solutions, private query labels, or prior
solution notes. The program below was reconstructed from the three examples in
`challenge.json`.

## Revision 0 — establish a failing executable check

I wrote a small pytest that imports `solve/solution.py` and compares its result
with all three visible training outputs. The untouched template failed with
`NotImplementedError`, which established that the check exercised the missing
solver rather than passing vacuously.

## Visible structure and hypothesis

Every input has a top region followed by an all-zero horizontal row. In the top
region, columns made entirely of 9 split the region into panels. Each panel has:

- exactly one additional 9, treated as an anchor;
- cells of one ordinary color, treated as a stencil relative to that anchor.

Below the all-zero row, ordinary colored cells act as seeds. For each seed, I
translate every same-color stencil offset from its visible top anchor to the
seed and paint the in-bounds translated cells onto an otherwise blank grid.
The output keeps the input dimensions; the library, separator, and original
seed cells are not copied automatically.

Concrete checks from the examples supported the relative-offset reading rather
than a geometric-center reading. For example, in training example 0 the first
panel's 9 is visibly off the panel center; translating its three color-1 cells
from that 9 to each lower color-1 seed reproduces the six output 1s. The other
colors and examples behave the same way, including clipping at grid boundaries.

Alternatives rejected from the visible pairs:

- Copying or moving the body seeds cannot explain the multi-cell output shapes.
- Treating a panel's geometric center as the anchor disagrees with the visible
  off-center 9s.
- Copying the top patterns verbatim cannot explain why every output pattern is
  positioned around lower same-color cells.

## Revision 1 — parser and relative stencil stamping

I implemented a rectangular-grid parser that finds the first all-zero row,
finds full-height 9 divider columns above it, extracts one anchor and one color
per panel, and stores colored-cell offsets from the anchor. It then scans lower
body cells in row-major order and stamps matching offsets into a blank output,
clipping translated cells that leave the grid. Malformed panel structure raises
an explicit `ValueError` rather than silently inventing an interpretation.

Remaining uncertainty is limited to overlap semantics that the visible pairs do
not force: the implementation uses deterministic row-major assignment. In the
shown examples, this reproduces all labels exactly.
