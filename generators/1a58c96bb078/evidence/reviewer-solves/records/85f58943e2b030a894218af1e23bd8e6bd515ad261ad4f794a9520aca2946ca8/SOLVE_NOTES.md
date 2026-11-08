# Solve notes

## Revision 1

The first row behaves as a column-by-column legend. In every demonstration,
cyan cells (`8`) below a nonzero first-row cell become that header color.
Cells below a zero header remain unchanged, including cyan cells. Unrelated
body colors also remain unchanged, so this is not a reconstruction from the
legend: it is a conditional replacement on a copy of the input.

Implementation: copy the grid; for rows after row 0, replace a value of `8`
with `grid[0][column]` only when that header is nonzero.

I had already inspected and repaired this task's generator before this required
post-repair solve, so this is an exposed visible-example solve, not a blind one.
I did not consult the Racket rule or any reference solution during this solve.
