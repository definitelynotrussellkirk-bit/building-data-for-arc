# Solve work log

## Earlier exposure

I had not opened this task's generator, canonical rule, reference solution, private
query labels, audit material, or prior solution notes before this solve. I used only
the visible examples emitted by `python3 review.py blind prepare` and the generated
`solve-blind/README.md`.

## Revision 1 — common-background overlay

The input consists of two same-sized panels separated by a solid row of color 7.
I compared corresponding cells in the two panels. In every training example, the
output is color 8 exactly where **both** panel cells are background color 0; every
cell occupied in either panel becomes 0. For example, train 0 row 0 has both cells
zero only at columns 1 and 2, matching the two output 8s. The same check explains
all output positions in the other rows and examples.

I considered XOR, equality/XNOR, union, and intersection of the nonzero masks.
They fail immediately on train 0 row 0: the two panels agree at all four cells,
but only their two shared-zero positions are marked. Thus the operation is the
intersection of the two background masks (equivalently, the complement of the
union of foreground masks), recolored azure.

The program locates the centered solid nonzero separator row, pairs rows above and
below it, and emits 8 when both values are 0, otherwise 0. Remaining uncertainty is
low: all five visible examples use the same layout and relation, though the checker
cannot reveal masked-query correctness.
