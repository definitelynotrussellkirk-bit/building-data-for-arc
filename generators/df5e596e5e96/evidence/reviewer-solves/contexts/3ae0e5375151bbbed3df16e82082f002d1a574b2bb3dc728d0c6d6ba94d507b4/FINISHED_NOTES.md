# Solve work log

## Exposure

Before this solve I had read only the packet-level start/duties documentation and
the visible examples printed by `blind prepare`. I did not inspect any generator,
canonical rule, reference solution, private labels, or prior task-specific notes.

## Hypothesis and probes

The 5×29 input decomposes into five 5×5 panels at column starts 0, 6, 12, 18,
and 24. Each panel contains one non-background shape; input colors vary but the
output depends only on shape geometry. The 5×5 output is a symmetric pairwise
relation matrix:

- diagonal 8;
- 1 when two shapes are identical after translation;
- 2 when a nonzero quarter-turn maps one shape to the other;
- 3 when a reflection, optionally followed by a rotation, maps them;
- 0 when no dihedral transform maps them.

I normalized each shape to its top-left occupied coordinate, enumerated the four
rotations, and enumerated one reflection followed by all four rotations. This
exactly reproduced every cell of all three visible training outputs. In
particular, the repeated translated shapes explain label 1, the endpoint-hook
rotations explain label 2, and opposite-handed hooks explain label 3; interior
hooks remain unrelated and receive 0.

## Implementation and uncertainty

`solution.py` infers the number of H×H panels from `W = N*H + (N-1)`, ignores
foreground color, and computes the relation matrix. The only remaining uncertainty
is whether a hidden episode could contain a highly symmetric shape that is both a
rotation and reflection match; the visible examples establish the precedence
identity → rotation → reflection, which the implementation follows.
