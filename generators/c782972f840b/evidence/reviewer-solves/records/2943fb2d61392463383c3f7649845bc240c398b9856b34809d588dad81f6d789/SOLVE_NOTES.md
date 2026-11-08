# Solve work log

This is a human work log for the post-repair episode. I had already studied the
assigned task while repairing its generator, so this is **not blind** and I will
report earlier exposure as `yes`. During this solve episode I used only the
visible `solve/challenge.json`; I did not reopen the generator, Racket rule,
private labels, or earlier solution explanations.

## Hypothesis 1

Each nonzero 4-connected component is one object. Sort objects by the top-left
cell of their bounding box. With `N` objects, emit an `N x N` symmetric relation
matrix:

- diagonal: 9;
- same shape up to quarter-turn rotation and same color: 6;
- same rotation-shape but different colors: 4;
- different rotation-shapes but same color: 2;
- otherwise: 0.

The three visible examples support this: matrix size equals object count, all
diagonals are 9, color-only pairs carry 2, rotated-shape-only pairs carry 4,
and the first example contains a pair carrying 6. I will implement connected
components and rotation canonicalization directly, then check all visible pairs.
