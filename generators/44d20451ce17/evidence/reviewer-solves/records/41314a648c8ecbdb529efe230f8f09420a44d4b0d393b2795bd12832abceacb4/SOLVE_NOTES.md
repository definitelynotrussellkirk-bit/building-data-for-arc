# Solve work log

## Exposure and constraints

I had already inspected this task's generator and canonical rule during the repair phase, so this is an exposed post-repair solve (`earlier_rule_exposure=yes`). During this solve I used only `challenge.json`, my own Python, and visible-example feedback. I did not reopen the Racket rule, generator source, reference solutions, private query labels, or earlier solution explanations.

## Revision 1

Visible examples support one column-wise transformation:

- Collect every column containing at least one color-1 cell.
- Erase all original color-1 cells to 0.
- Put exactly one color-1 cell in the bottom row of every collected column, overwriting the prior bottom value there.
- Preserve every non-1 cell outside those bottom destinations.

This explains the repeated vertical stack in example 1 collapsing from three 1s to one, and examples 0/2 show that the destination can overwrite a 5. A weaker "move each 1 downward independently" rule would preserve multiplicity and therefore fails example 1. A "fall until the nearest support" rule would stop above the 5 structure and fails all three examples. The implementation uses the presence of a 1 in each column, not the number or original row.

Remaining uncertainty is limited to masked queries; all visible examples have rectangular nonempty grids. The code also returns an empty grid unchanged defensively.
