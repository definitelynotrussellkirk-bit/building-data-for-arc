# Solve notes

Human work log from the visible examples only. I did not reopen the generator,
canonical rule, reference solutions, or private query labels during this solve.

## Hypothesis

Every input has a horizontal separator made entirely of color 9. The lower half
starts blank. Preserve the upper half and separator, then fill the lower half by
reflecting the upper rows vertically across the separator: the row immediately
above the separator becomes the row immediately below it, and so on. Columns and
colors remain unchanged.

This explains all three demonstrations, including example 1 where the blank row
in the upper half must also appear at the corresponding reflected position. The
implementation locates the full-9 row rather than assuming a fixed height.
