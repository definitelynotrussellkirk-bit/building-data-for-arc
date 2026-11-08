# Post-repair visible-only solve notes

Earlier exposure: yes. I authored/reviewed this generator before the solve episode, but during this solve I used only `solve/README.md` and `solve/challenge.json`; I did not reopen the generator, Racket rule, reference solutions, or private labels.

## Visible observations

- Every input and output keeps the same odd square shape and colors {0, 5, 7}.
- Gray-cell count is preserved in all three visible examples: 11 input gray cells become an 11-cell centered line.
- Two parallel black divider lines reveal the track direction. Two vertical dividers imply a vertical gray output line; two horizontal dividers imply a horizontal gray output line.
- The output moves the parallel walls to one cell on either side of the center axis.
- A full perpendicular black crossbar remains through the center. The gray line overwrites the middle part of that crossbar/axis.
- The gray line is centered and has exactly as many cells as the input gray motif.

## Algorithm

1. Count all cells of color 5.
2. Detect divider rows/columns using the visible convention: a divider is all 0/5, or contains more than half zeros.
3. If at least two divider columns are present, construct a vertical-track output; otherwise construct a horizontal-track output.
4. Start with all 7s. Draw the two new parallel zero walls at center-1 and center+1, and draw the perpendicular center crossbar.
5. Draw the centered gray line of the preserved count along the track direction.

This is intentionally input-pure and does not use any fixed size-to-line-length table.
