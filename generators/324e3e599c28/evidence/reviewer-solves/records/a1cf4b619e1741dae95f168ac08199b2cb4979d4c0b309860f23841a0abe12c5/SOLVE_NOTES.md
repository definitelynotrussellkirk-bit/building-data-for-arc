# Solve work log

## Exposure declaration before solving

I had not opened task `324e3e599c28`'s generator, Racket rule, notes, reference
solutions, audit evidence, or private labels. I used only the visible examples
printed by `review.py blind prepare` and `solve-blind/challenge.json`.

## Revision 1 — point reflection around the 9 cell

**Hypothesis.** Color 9 is a pivot. Every other nonzero cell is retained and a
second copy is placed at its 180-degree point reflection through the pivot:
`(r, c) -> (2*pivot_r-r, 2*pivot_c-c)`.

**Evidence from the visible examples.**

- Example 0: the two-by-two block southwest of 9 reappears northeast with both
  axes reversed, exactly as point reflection predicts.
- Example 1: the horizontal `6,2,6` motif left of 9 reappears to the right.
- Example 2: the vertical `8,1,8` motif below 9 reappears above it.

A simple mirror across a row, column, or diagonal fails at least one example;
translation alone also cannot explain all three orientations. The implementation
copies the input, locates the unique 9 pivot, and reflects every nonzero,
non-pivot cell when the reflected coordinate is in bounds.

**Predicted queries.**

- Query 0 gains cells `(6,6)=8`, `(7,6)=1`, `(7,7)=8`, `(8,6)=1`.
- Query 1 gains three color-7 cells at row 4, columns 2 through 4.

No deliberate teaching negative or diagnostic-only revision was used.
