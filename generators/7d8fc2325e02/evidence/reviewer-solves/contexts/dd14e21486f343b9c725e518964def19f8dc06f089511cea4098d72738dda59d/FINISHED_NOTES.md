# Solve notes

## Visible-only hypothesis

The uniform fifth row separates two aligned 4-row panels. The output has the
same shape as either panel. At each aligned coordinate, the output is 3 when
either panel cell is nonzero and 0 only when both are zero.

Evidence from the visible examples:

- Train 0 contains top-only, bottom-only, overlap, and jointly empty positions;
  the output follows occupancy OR in all four cases.
- Train 1 rules out copying only one panel because both top-only and bottom-only
  cells become 3.
- Train 2 rules out XOR because overlap cells remain 3.
- Query 0 uses color 3 for the panels and separator alike, so the split must be
  positional; color identity is not the rule.

No failed revision was needed. I implemented the direct aligned occupancy OR.
I had seen the task rule earlier during the repair assignment, so this is not a
blind solve; I did not reopen or consult a reference while writing this solve.
