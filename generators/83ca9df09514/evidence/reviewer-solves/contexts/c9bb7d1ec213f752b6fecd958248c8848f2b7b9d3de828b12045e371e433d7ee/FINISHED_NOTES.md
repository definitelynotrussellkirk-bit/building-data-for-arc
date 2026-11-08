# Solve work log

This is a human work log. I had earlier exposure to the task during the generator
review, so this is not a blind solve. During this solve I used only the prepared
visible examples and did not reopen the generator, Racket rule, reference
solutions, or private labels.

## Revision 1 — template-color substitution

Across all three visible examples, one row is uniquely densest and spans all
columns. Repeated colors in that row partition columns into groups. Every other
nonempty row is sparse: its nonzero cells pair a template color at that column
with a destination color. The output fills every column in the same template
color group with that destination color. Empty rows stay empty, and the dense
template row stays unchanged.

Checks against the visible examples:

- Example 0: template `[9,5,9,5,1,1,5,9]`; the sparse first row reveals
  `9→1`, `5→4`, `1→5`, producing `[1,4,1,4,5,5,4,1]`.
- Example 1: row 8 is the template; row 3 reveals `7→2`, `6→4`, `2→6`,
  matching the displayed output.
- Example 2: row 5 is the template; each sparse row supplies all three group
  mappings, including reveals beyond the first three columns.

Alternative rejected: filling by nearest visible key cell. Equal output colors
occur at all columns sharing a template color even when they are separated, so
this is a group substitution rather than geometric interpolation.

Remaining uncertainty: none on the visible examples. The implementation chooses
the uniquely densest row, preserves empty rows, and applies the inferred mapping
independently to every sparse row.
