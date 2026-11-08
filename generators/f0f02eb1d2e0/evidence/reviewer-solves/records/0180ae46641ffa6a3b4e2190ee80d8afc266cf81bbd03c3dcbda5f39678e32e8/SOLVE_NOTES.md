# Visible-only solve notes

This is a human work log. I had already reviewed the assigned generator before this exposed solve, so earlier rule exposure is **yes**. During this solve I did not reopen the generator, Racket source, reference solutions, private labels, or earlier solution explanations.

## Hypothesis from the visible examples

Treat each nonzero color independently. If a color occurs exactly three times and those cells use exactly two rows and exactly two columns, the three cells are three corners of an axis-aligned rectangle. Copy that color into the one missing corner. Leave every other color pattern unchanged.

Evidence:

- Train 0: both colors have three rectangle corners, and each gains exactly its missing fourth corner.
- Train 1: color 4 has three corners and is completed; color 8 uses three rows, so it is unchanged.
- Train 2: colors 2, 3, and 5 are completed. The two-cell color 8, the collinear color 9, and the three-row color 7 stay unchanged.
- Train 3: colors 1, 2, and 3 are completed. Bent/diagonal patterns for colors 7, 8, and 9 stay unchanged.

## Implementation plan

Copy the grid, group coordinates by nonzero color, require exactly three cells and exactly two distinct rows/columns, compute the four Cartesian-product corners, and fill the unique missing corner only when it is background 0. This preserves dimensions and all existing cells.
