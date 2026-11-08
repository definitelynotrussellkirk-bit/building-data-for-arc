# Solve work log

I had not opened this task's generator, rule, notes, reference solution, private
labels, or audit records before solving. I used only the visible examples printed
by `python3 review.py blind prepare`.

## Revision 1 — isolated-cell hypothesis

Across all three training examples, every color-1 cell with no orthogonal
color-1 neighbor changes to color 2. Every color-1 cell belonging to a horizontal
or vertical component of size at least two remains color 1. Diagonal contact does
not count: in training example 1, `(1, 0)` is diagonal to `(0, 1)` yet changes to
2. Other colors, including the lone color-3 marker, remain unchanged.

I implemented exactly that local rule: copy the grid, inspect each 1-cell's four
orthogonal neighbors in the original input, and recolor it to 2 only when none is
1. This also predicts that each visible query keeps its multi-cell 1-components
and recolors only singleton 1s. Remaining uncertainty is limited to whether an
unseen component topology was intended to use a larger object-level criterion;
the visible examples distinguish orthogonal from diagonal adjacency and fully
support the local singleton rule.
