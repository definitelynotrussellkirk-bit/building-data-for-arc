# Post-repair visible-only solve notes

Earlier exposure: yes. I repaired this generator before the separate solve episode, so this is not blind and I already knew the intended family of rule. During this episode I used only the prepared visible examples and did not consult the Racket source, generator source, private labels, or prior solution files.

## Hypothesis

Treat zero cells as four-connected regions. A zero region changes only when it is fully enclosed away from the canvas border and every cardinally adjacent nonzero cell has the same color. Fill the entire qualifying region with that color. Leave exterior/open regions and regions with mixed-color boundaries unchanged.

The examples distinguish four-connectivity from diagonal contact, show a one-cell enclosure, and show that a diagonally placed different color does not count as part of the boundary.

## Implementation

Flood-fill each unseen zero region, record whether any cell touches the canvas border, and collect colors seen across cardinal edges. Fill only when `touches_border` is false and the collected set has size one.
