# Visible-only solve notes

Earlier exposure is **yes** because I repaired this task before this solve. During this solve I did not reopen the generator, canonical rule, reference solution, or private labels; I used only the examples printed by `review.py solve prepare`.

## Hypothesis

The three full color-5 columns divide each 3x15 input into four 3x3 panels: A, B, X, Y.

1. Infer the square symmetry taking A to B. The examples show rotations/reflections rather than recoloring.
2. Apply the same symmetry to X.
3. Overlay transformed X with Y cell by cell:
   - if one cell is zero, keep the other;
   - if both nonzero values match, keep that value;
   - if both are nonzero and differ, output 9.

This explains every displayed output, including the four visibly exercised cases in each generated example: X-only, Y-only, equal overlap, and unequal overlap.

## Implementation choice

Enumerate the eight D4 transforms in a fixed order, select the first exact A→B match, transform X, then perform the merge. The first-match convention is deterministic if a displayed A shape happens to have more than one symmetry.
