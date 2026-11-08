# Solve notes — 5419b6df2873

This is a human work log based only on the visible prepared examples. I had already inspected this task's rule and generator during the required repair phase, so this is an exposed post-repair solve rather than a blind solve; I did not reopen either source while solving.

## Hypothesis

Every nonzero cell in the first row is a column marker. Start from an all-zero grid with the same shape, then copy each top-row marker's color down every row in that column. Lower-row input cells in unmarked columns are distractors and are erased rather than preserved.

Evidence from the three visible demonstrations:

- Example 0 has top-row markers 9, 5, and 8; each becomes a full-height stripe. The extra lower-row 8 in column 3 disappears.
- Example 1 has top-row markers 8 and 5; both become stripes. The lower-row 5 in column 0 disappears.
- Example 2 has top-row markers 4, 8, and 3; all become stripes. The lower-row 4 in column 4 disappears.

The same single rule handles both query grids without special cases. I implemented it directly and will check the visible examples once.
