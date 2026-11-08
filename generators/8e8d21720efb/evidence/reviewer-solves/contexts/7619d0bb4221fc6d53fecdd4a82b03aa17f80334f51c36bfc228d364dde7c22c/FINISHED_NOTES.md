# Solve work log

This is a human work log. I had already inspected the selected generator and its
rule during the repair phase, so earlier rule exposure is **yes**. During this
solve I used only the freshly prepared visible examples and did not reopen the
generator, Racket rule, private labels, or a reference solution.

## Revision 1 — same-colour cardinal support

Across all three demonstrations, every isolated nonzero cell becomes 0. Cells
survive exactly when at least one orthogonal neighbor has the same color:

- Example 0 keeps the color-4 three-cell L and the horizontal color-5 pair,
  while isolated colors 9 and 2 disappear.
- Example 1 keeps a vertical color-5 pair and horizontal color-1 pair. The two
  color-7 cells are diagonal, so both disappear, as do the isolated 9 and 3.
- Example 2 keeps the two horizontal pairs and removes the isolated 1 and 3.

Hypothesis: create a zero grid of the same shape and copy each nonzero cell only
when an up/down/left/right neighbor has the same value. Diagonal contact and
adjacency to a different color do not count.

For query 0 this predicts retaining the vertical 9 pair and horizontal 6 pair,
while removing the isolated 6, 5, 2, and diagonal 4 pair. For query 1 it retains
the color-4 L and vertical color-6 pair and removes the isolated 1.

No alternative visible-example rule remained necessary after checking all three
examples. Hidden-query correctness is unknown until independent scoring.
