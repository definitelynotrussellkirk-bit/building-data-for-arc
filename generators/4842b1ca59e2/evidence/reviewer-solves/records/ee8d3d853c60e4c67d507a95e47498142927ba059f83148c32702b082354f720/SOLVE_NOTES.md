# Solve work log

Earlier exposure before this episode: none to this task's rule, generator, labels,
or prior solution notes. I used only the visible examples produced by the blind
challenge.

## Revision 1 — topmost nonzero cell controls its column

Observation: every output keeps the input dimensions. Each input column that
contains at least one nonzero cell becomes a solid vertical stripe; empty columns
stay zero. The stripe color is the topmost nonzero color in that same column.

Evidence from the visible examples:

- Example 0, column 1 contains 7 above 6 and becomes all 7; column 4 contains 6
  and becomes all 6.
- Example 1, column 1 contains 4 above two 3s and becomes all 4; column 2 contains
  3 above two 9s and becomes all 3; column 5 contains 9 and becomes all 9.
- Example 2 repeats the same ordering distinction in column 1 (7 above 4).

I briefly considered choosing a representative column separately for each color,
but example 1 is better explained column-by-column, and query 0 deliberately puts
opposite color orderings in columns 0 and 5. The implementation scans each column
from top to bottom, takes the first nonzero value, and repeats the resulting row
for the full height.

Remaining uncertainty: the visible examples are rectangular and use zero as the
background. I reject ragged grids explicitly rather than inventing a convention.
