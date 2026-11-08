# Solve work log

## Exposure

I had not opened this task's generator, canonical rule, reference solution, private labels, prior solve notes, or any repair/audit target before solving. I used only the visible challenge and local Python-style coordinate inspection.

## Observation and hypothesis

At first the examples looked like removal of noisy fragments or compression of vertical runs. Comparing coordinates by **column** made the invariant exact:

- Example 0 has two yellow cells in each occupied column; the output keeps the row-0 cell.
- Example 1 has three yellow cells in each occupied column; the output keeps the smallest-row cell.
- Example 2 has 13 occupied columns, and the 13 output cells are exactly the smallest-row yellow cell of each column.

Hypothesis: independently for every column, preserve the topmost nonzero cell and replace every lower nonzero cell with background. Empty columns remain empty. Shape and surviving color are unchanged.

## Revision 1

Implemented a column scan from top to bottom, copying the first nonzero value and stopping for that column. This deliberately does not depend on run length, connected components, or the foreground being specifically color 4.

Remaining uncertainty before the visible check: none on the demonstrations; masked-query labels remain unavailable by design.
