# Solve work log

## Prior exposure

Before this solve I had read only the packet-level instructions and the visible
challenge prepared by `review.py blind prepare`. I had not opened this task's
generator, Racket rule, reference solution, private query labels, prior solution
notes, or audit evidence.

## Revision 1 — overlap of the two blank masks

The input is two equal-width panels placed side by side. The output has the same
height and half the input width. In every training example, a gray `5` appears
exactly where the corresponding cell is background `0` in **both** panels;
all other positions are `0`.

I checked this against every marked training coordinate:

- Example 0: row 0 has common blanks at columns 1 and 4, and row 3 at columns
  1 and 6; these are exactly the four output marks.
- Example 1: the common blanks are `(4,0)`, `(6,0)`, and `(7,1)`.
- Example 2: the common blanks are `(3,0)`, `(3,1)`, and `(3,3)`.

I also considered XOR, equality of the colored masks, and overlap of the colored
cells. Each is contradicted by example 0: colored overlap at `(0,2)` is not
marked, while common background at `(0,1)` is marked.

The program therefore splits each row at the midpoint and emits `5` only when
both aligned cells are zero. Remaining uncertainty is limited to whether a
nonzero background could occur in unseen instances; all visible examples use
zero as background, so I retain the direct visible rule rather than inventing
palette inference.
