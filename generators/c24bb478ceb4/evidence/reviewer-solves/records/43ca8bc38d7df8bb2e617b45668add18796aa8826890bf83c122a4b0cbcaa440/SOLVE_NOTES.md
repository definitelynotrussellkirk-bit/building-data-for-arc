# Post-repair solve notes — c24bb478ceb4

This is a human work log based on the visible examples shown by `solve prepare`.
I had earlier exposure to the task rule and generator while performing the assigned
repair, but I did not consult the generator, Racket rule, canonical answers, private
query labels, reference solutions, or prior solution explanations during this solve.

## Visible-example hypothesis

Each nonzero color occurs at exactly three positions. Those positions use two rows and
two columns and therefore form three corners of an axis-aligned rectangle. The output
copies the input and adds the missing row/column combination in the same color.
Different colors are handled independently.

Visible checks:

- Example 0: color 5 uses rows 3 and 5, columns 1 and 4, so `(3,1)` is added; color 6
  uses rows 4 and 5, columns 0 and 6, so `(4,0)` is added.
- Example 1 demonstrates three independent rectangles and different missing corners.
- Example 2 adds `(6,1)` for color 2 and `(4,5)` for color 3.

The implementation groups cells by color, takes the two unique rows and columns, and
writes the one absent Cartesian-product position. It leaves malformed color groups
unchanged rather than guessing.
