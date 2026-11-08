# Solve work log

## Prior exposure

Before this isolated solve I had already inspected and repaired this generator and knew that its task involved bar lengths, a top-row color-5 query marker, duplicate-length handling, and a square/modulo encoding. I did not consult the generator, Racket rule, reference output, private labels, or earlier solution notes after `solve_episode.py prepare` rebound the episode to the repaired source.

## Revision 1

From the four visible training examples:

- The top-row `5` selects the output column.
- Every nonempty lower row is a bar; its length is the number of nonzero cells.
- When no eligible length repeats, a bar of length `L` writes `(L - 1)^2 mod 10`.
- A lower bar containing color `5` is excluded when deciding which length is duplicated, but it still receives an output digit.
- When an eligible length `A` repeats, bars of another length `L` write `(L - A)^2 mod 10`; bars of length `A` keep the ordinary `(A - 1)^2 mod 10` code.

This explains every changed cell in all four examples, including training example 3: eligible length 4 repeats, so lengths 5, 4, and 2 produce 1, 9, and 4 respectively. I implemented exactly that rule, preserving all other cells. The remaining uncertainty is only how a malformed episode with several different repeated lengths would select an anchor; the visible curriculum presents one anchor, so the implementation uses the first repeated eligible length in row order.
