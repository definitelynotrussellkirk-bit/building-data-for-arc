# Solve work log

## Exposure declaration

Before this visible-only solve I had already inspected the assigned generator while
repairing it, including its intended transformation. This attempt is therefore not
blind. After `prepare` I used only the displayed examples and solve files; I did not
consult the Racket rule, generator source, reference solutions, private query labels,
or earlier solution explanations.

## Revision 1 — positional occupancy union

The inputs consistently have two four-row panels, rows 0–3 and 5–8, separated by a
uniform row 4. The output has four rows and the same width. I hypothesized that each
output cell is green (`3`) exactly when either aligned panel cell is nonzero.

Visible probes distinguish this from nearby alternatives:

- Train 0 at output `(0,2)`: top is `0`, bottom is `1`, and output is `3`, ruling out
  copy-top and occupancy-AND.
- Train 0 at `(0,0)`: both aligned cells are nonzero and output is `3`, ruling out XOR.
- Train 0 at `(1,3)`: both are zero and output is `0`, ruling out constant fill.
- Train 1 uses different panel and separator colors, while query 0 uses color `3` in
  both panels and the separator; the row positions, not color identities, define the
  roles.

I implemented the four-by-width cellwise occupancy OR, ignoring the separator row.
The remaining uncertainty is only private-query scoring; the visible examples expose
all four Boolean occupancy cases.
