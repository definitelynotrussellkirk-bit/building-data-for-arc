# Solve work log

## Exposure declaration before solving

I had not opened task `9db8deba5903`'s generator, Racket rule, prior notes,
private labels, or solution explanations. I had only read the packet-level
instructions and `solve-blind/challenge.json`.

## Revision 1 — four rotations in a 2×2 canvas

**Observation.** Every output is twice the input height and twice the input
width. Splitting each output into four input-sized quadrants shows:

- upper-left: the original input,
- upper-right: a 90° counter-clockwise rotation,
- lower-left: a 180° rotation,
- lower-right: a 90° clockwise rotation.

The first 3×3 example alone does not distinguish clockwise from
counter-clockwise in the side quadrants because that particular grid has extra
rotational symmetry. The nonsymmetric 5×5 and 6×6 examples distinguish them.
I verified the quadrant relation directly with small Python/Numpy comparisons;
I did not inspect any reference implementation or labels.

**Implementation.** `solution.py` constructs the three rotations using Python
list operations and concatenates the quadrants. The visible tasks are square,
which is also the shape for which all four rotations tile into one rectangular
2×2 canvas without mismatched row counts.

**Alternatives considered.** Mirror/reflection rules were rejected because the
5×5 quadrants match quarter-turn rotations exactly. Repeating the input in all
quadrants was rejected by those same examples.

**Remaining uncertainty.** The visible examples establish the rule strongly for
square grids. If hidden inputs were rectangular, the displayed 2×2 arrangement
would need a convention for unequal rotated dimensions; no such case is shown.
