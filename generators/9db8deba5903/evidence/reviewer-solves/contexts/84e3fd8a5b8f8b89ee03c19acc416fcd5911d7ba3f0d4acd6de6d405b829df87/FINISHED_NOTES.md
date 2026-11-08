# Solve work log

## Exposure declaration before solving

I had not opened task `9db8deba5903`'s generator, Racket rule, reference
solutions, audit records, or earlier solution explanations. I used only
`solve-blind/challenge.json` and local Python comparisons against the four
visible training outputs.

## Revision 1 — four rotations in a 2×2 pinwheel

Observation: every output is twice the input height and width. The upper-left
quadrant is the input unchanged. On the asymmetric 5×5 examples, the upper-right
quadrant is the input rotated 90 degrees counter-clockwise, the lower-left is a
180-degree rotation, and the lower-right is a 90-degree clockwise rotation.
The first 3×3 example is less diagnostic because its clockwise and
counter-clockwise rotations coincide, so I used the larger examples to determine
the direction.

Hypothesis: form a 2×2 pinwheel of successive counter-clockwise quarter-turns:
`[[R0, R90], [R180, R270]]`.

Probe: imported `solve-blind/solution.py`, ran `solve` on all four visible
training inputs, and compared exact nested lists to their outputs. All four
matched, with predicted sizes 6×6, 10×10, 10×10, and 12×12.

Implementation: `_rotate_ccw` uses transpose plus row reversal; `solve` builds
all four rotations and concatenates corresponding rows. No colors, dimensions,
or task-specific constants are hard-coded. Remaining uncertainty is limited to
whether non-square inputs are in-domain; the visible tasks are square and the
quadrants must share dimensions for this exact layout.
