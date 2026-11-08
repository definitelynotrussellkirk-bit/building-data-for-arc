# Solve work log

## Exposure declaration before solving

I had already inspected the task's canonical rule and repaired its generator before this required post-repair solve, so this is **not blind**. During this solve phase I consulted only `solve/challenge.json`, the local solution file, and visible-only checker feedback; I did not reopen the generator, Racket source, reference solution, or private labels.

## Revision 1 — full feature-signature match

Visible examples show one blue component acting as a key. The recolored object is not necessarily an exact geometric copy: in training example 1 the blue and recolored color-7 objects have different normalized masks but the same cell count and the same reflection behavior. Training example 2 recolors two objects, so the transformation applies to every match rather than only the first.

The three demonstrations are consistent with comparing each non-blue 4-connected monochromatic component to the blue component by:

1. area (number of cells),
2. number of enclosed background regions inside its bounding box, and
3. reflection-symmetry class (horizontal only, vertical only, both, or neither).

I implemented 4-connected component extraction, translation-normalized masks, enclosed-hole counting, row/column reflection tests, and recoloring every non-blue component with the same triple to color 8. Mismatches and the blue seed remain unchanged.

Remaining uncertainty before checking: whether reflection class means the exact pair of horizontal/vertical booleans or only their count. The demonstrations include asymmetry and directional symmetry contrasts, so I used the exact four-way class.
