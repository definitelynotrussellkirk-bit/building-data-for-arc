# Exposed post-repair solve

Earlier exposure: yes. I worked on this task's generator and rule before this
episode. This is not a blind solve. During this solve I read only the public
`solve/README.md` presentation and used my own Python solution; generator source,
reference programs, private labels and prior solution notes stayed closed.

## Visible observations and first hypothesis

Example 0 is 10×13 in and out. Every output row is identical. Column 3 has
several input cells of color 2 and becomes zero; column 7 contains several
colors and also becomes zero. Columns with one occupied input cell become
full vertical stripes, retaining that cell's color. This distinguishes counting
occupied cells from counting distinct colors.

Example 1 is 16×16 in and out. The tall repeated-color column 11 disappears,
while isolated cells in other columns become full-height stripes. This also
rules out preserving already colored distractor cells in the output.

Example 2 is 7×7 in and out. The isolated 6 in column 1 and 8 in column 4 fill
their columns; all other columns remain zero.

My first candidate therefore counts nonzero cells independently in each column,
uses the sole cell's color exactly when the count is one, and emits that same
row of column colors for every output row. It preserves the input dimensions
and does not modify the supplied grid. The two visible query inputs are 8×8
and 13×14; their output labels are unknown.

No deliberately wrong solver was submitted and no failed experiment is invented.
The next action is the genuine first solution check against the visible examples.
