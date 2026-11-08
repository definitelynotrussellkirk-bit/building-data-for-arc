# Solve work log

## Exposure declaration

I had already inspected this task's generator and canonical rule while repairing it,
so this is an exposed post-repair solve. During this solve episode I used only the
visible examples in `solve/README.md`; I did not reopen the generator, Racket source,
reference solutions, or masked labels.

## Revision 1 — midpoint completion

The output shape and all existing cells are preserved. For every nonzero color in the
visible examples, the input has exactly two endpoints in one row or one column. The
output adds exactly one same-colored cell at their integer midpoint:

- example 0: vertical 7 endpoints at rows 0 and 4 gain row 2;
- example 1: horizontal and vertical pairs of three different colors are handled
  independently;
- example 2: horizontal 7 endpoints at columns 2 and 6 gain column 4.

I implemented a color-position scan, required exactly two aligned cells and an even
separation, then filled an empty midpoint while preserving the input. The guards make
this safe for malformed/non-triggering colors without inventing changes. I expect the
same independent midpoint completion on both masked queries.
