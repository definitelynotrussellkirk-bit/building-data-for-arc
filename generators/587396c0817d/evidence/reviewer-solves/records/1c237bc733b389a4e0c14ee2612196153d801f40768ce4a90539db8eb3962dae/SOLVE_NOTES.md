# Solve work log

## Prior exposure disclosure

Before this prepared solve I had already inspected the repaired generator and its canonical rule while performing the review. I therefore mark `earlier-exposure yes`. During this solve I did not reopen or consult the generator, Racket rule, reference solutions, private labels, or prior solve notes; I used only the freshly materialized visible examples in `challenge.json`.

## Visible-example hypothesis

Every output keeps the input dimensions and uses only background color 7 and bar color 8. A row without a 6 is erased to all 7. For a row with a 6:

1. Read the columns of every non-7 cell from left to right.
2. Count those cells; this count is the output bar length.
3. Find the zero-based rank of the 6 within that ordered non-7 list.
4. Place a contiguous bar of 8s so that the bar cell at that same rank lies in the original column of the 6. Equivalently, `start = column_of_6 - rank_of_6`.

Visible checks that distinguish this from simply starting at the 6:

- Train 0 row 0 has five non-7 cells before/including the 6 at ordered rank 2 and nine non-7 cells total, so the seven? Correction after recount: it has seven non-7 cells total and rank 2, yielding start column 2 and a seven-cell bar at columns 2..8, exactly as shown.
- Train 1 row 6 has four non-7 cells, with the 6 at ordered rank 1 in column 1, so the bar starts at column 0 and spans columns 0..3.
- Train 2 row 3 has six non-7 cells, with the 6 first among them in column 1, so the bar starts at column 1 and spans columns 1..6.

The implementation applies this row-local rule and preserves shape. It defensively ignores out-of-grid columns, although every visible construction keeps the computed bar in bounds.
