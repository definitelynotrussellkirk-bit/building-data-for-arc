# Solve work log

## Exposure declaration before solving

This is the required post-repair solve. I had already inspected and modified the
selected generator during the review, so earlier rule exposure is **yes**. After
`python3 review.py solve prepare`, I did not reopen the generator, Racket rule,
reference solutions, private query labels, or prior solution explanations. I
used only the visible challenge and local Python probes.

## Revision 1 — aligned occupancy XOR

**Visible hypothesis.** The full color-4 column separates two equal-width
panels. For every position in the left panel, compare it with the aligned
position in the right panel. Output color 2 exactly when one side is nonzero and
the other is zero; output 0 when both are empty or both are occupied. Foreground
color identities are irrelevant.

**Evidence.** In train example 0, row 0 column 1 is occupied only on the left and
becomes 2, while column 3 is occupied on both sides and becomes 0. Train examples
1 and 2 change both panel colors and dimensions while preserving the same
occupancy comparison, ruling out fixed palette and fixed-size interpretations.

**Test-first probe.** A local visible-only regression script covered all three
training pairs, a palette-transfer input, and equal occupied occupancy. It first
failed on the untouched `NotImplementedError`, then passed after implementation.
No query output was available or used.

**Implementation.** Find the column that is entirely color 4, use its index as
the panel width, and construct an output of the input height by that width. Each
cell is 2 iff the corresponding left/right nonzero predicates differ.

**Alternatives considered.** Comparing exact colors is contradicted by examples
whose two foreground palettes differ. Overlaying or subtracting one fixed side
is contradicted by positions where left-only and right-only cells both become 2.

**Remaining uncertainty.** The visible examples consistently provide one full
separator and equal panel widths; the solver follows that presentation rather
than attempting to repair malformed grids.
