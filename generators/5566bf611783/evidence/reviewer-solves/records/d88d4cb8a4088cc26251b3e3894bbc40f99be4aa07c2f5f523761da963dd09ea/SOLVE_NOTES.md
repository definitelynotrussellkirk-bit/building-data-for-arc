# Visible-only solve notes

## Hypothesis

Color 5 is an impermeable wall. Its full lines and segments partition the grid
into 4-connected chambers. Existing 2 and 3 cells are votes within their own
chamber. Fill each zero in that chamber with the majority vote, preserving all
walls and marker cells. An exact 2/3 tie uses color 8.

## Evidence from the visible examples

- Example 0 has four chambers. The upper middle chamber has one 2 and becomes
  all 2; the lower middle has one 3 and becomes all 3. The left and right
  chambers likewise follow their local marker majorities.
- Example 1 shows that a marker of the losing color is preserved while the
  surrounding zeros take the chamber majority.
- Example 2 confirms that a partial horizontal wall segment still separates the
  two middle chambers because it connects full vertical walls; connectivity,
  not rectangular slicing, is the robust formulation.

## Implementation

Run a 4-neighbor flood fill over every non-5 component, count colors 2 and 3,
and replace only zeros with 2, 3, or 8 according to the comparison.
