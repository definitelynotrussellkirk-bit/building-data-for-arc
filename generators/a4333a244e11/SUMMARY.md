# a4333a244e11 — two-seed Manhattan Voronoi lessons

The input is a background-0 canvas with a one-cell margin around one complete
color-8 rectangular frame. Exactly two distinct-colored seeds occur inside the
frame. The selected canonical Racket authority fills each empty interior cell
with the color of its Manhattan-nearest seed; exact distance ties remain 0.
The frame and seeds are preserved.

Selected generator version: `3.1.0`. Canonical rule hash:
`d568e0e496cf`. The authority was not changed by this repair.

The sampler exposes six exact, observable axes:

- frame height `5..10` and frame width `7..14`;
- four two-color palette families spanning every non-background, non-frame ARC
  color;
- row, column, or diagonal seed alignment;
- tie-present or tie-absent Manhattan parity; and
- ascending or descending seed-color order in row-major seed position.

A deterministic four-profile schedule supplies three demonstrations per lesson:

1. diagonal / tie present / descending colors;
2. diagonal / no tie / ascending colors;
3. row / tie present / descending colors; and
4. column / tie present / descending colors.

Every three-of-four query rotation refutes five declared plausible rivals:
global position-sorted colors, Euclidean nearest-seed fill, lower-color tie
breaking, position-sorted colors only on axis-aligned cases, and lower-color tie
breaking only on axis-aligned cases. The fourth profile also broadens dimensions
by difficulty while preserving the full advertised override domain in every
band.

`tests/test_generator.py` is the task-local regression suite.
`workspace/reference_probe.py` is an independent, portable Python oracle and
optional real-Racket parity/audit tool; it does not replace the Racket label
authority.
