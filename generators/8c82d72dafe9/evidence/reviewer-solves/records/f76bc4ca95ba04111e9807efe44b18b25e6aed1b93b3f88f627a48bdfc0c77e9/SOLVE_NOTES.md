# Post-repair visible-only solve notes

This is a human work log. I had earlier rule exposure from repairing this same
task, so this episode is not blind. During this solve phase I used only the
prepared visible examples and did not reopen the generator, Racket source,
private labels, reference outputs, or prior solution explanations.

## Hypothesis

For every nonzero color, collect its cells in row-major input order. A color
that occurs exactly twice in different rows and different columns supplies two
diagonal corners of an axis-aligned rectangle. Draw the complete rectangle
border in that color on top of a copy of the input. Preserve all other cells.

Visible evidence:

- Train 0: the four-cell color 4 block remains unchanged; colors 7 and 8 become
  borders. Their borders cross, and later-first-seen 8 overwrites 7 at both
  crossings.
- Train 1: color 3 occurs twice in one column and remains only two cells; colors
  2, 9, and 6 are diagonal pairs and expand. The four-cell color 1 block remains.
- Train 2: color 5 occurs twice in one row and remains unchanged; the three-cell
  color 3 object remains; colors 9, 2, and 6 expand.
- Train 3: colors 4 and 2 expand, while four-cell color 3 remains. Their overlap
  again follows row-major first occurrence: later color 2 wins.

## Implementation choice

Use a dictionary populated by row-major scanning so insertion order represents
first occurrence. Compute all marker positions from the original input, then
paint qualifying borders in that order. This avoids accidentally treating newly
painted border cells as extra markers.

No alternate implementation revision was needed before the first check.
