# Post-repair visible-only solve log

This is a human work log. I had earlier exposure to the selected task's rule while
repairing its generator, but during this solve phase I used only the prepared
visible examples and did not reopen the generator, Racket source, reference
solutions, private labels, or previous solution explanations.

## Revision 1 — expanding keyed triangle

The first row is a color key. Below it, the input contains one contiguous vertical
cyan (`8`) line in a gray (`5`) field. The output discards the key row and keeps
the field gray outside the line's observed top/bottom interval. At the line's top
row the output contains only cyan. Each following row expands one column farther
left and right, copying those columns' values from the key row while leaving the
center cyan. Expansion saturates at half the grid width.

Checks against the visible examples:

- Example 0: centered line starts at row 5; radii 0..5 reproduce the full key on
  the last row while preserving cyan at column 5.
- Example 1: left-shifted line at column 4 ends at row 10; the output expands from
  rows 3..10 and leaves row 11 gray, so the interval comes from the observed line,
  not the grid bottom.
- Example 2: right-shifted line at column 8 likewise expands around the line rather
  than around the geometric center and stops before the final row.

Implementation: locate all cyan cells below row 0, infer the unique line column
and its top/bottom rows, then construct the triangular projection from the key.
