# Solve notes: d8d37830884c

## Visible evidence

Each output preserves the input's dimensions, zero background, and occupied
coordinates. Input colors are discarded. Every same-color 4-connected nonzero
component is recolored uniformly.

Across the three demonstrations, each component containing exactly six cells is
red (2), while components of every other observed cardinality are blue (1).
This explains both gray-only demonstrations and the third demonstration with
independent colors 6 and 7, so color identity is not part of the rule.

## Implementation

Scan the grid, flood-fill same-color nonzero components with four-neighbor
connectivity, then paint a fresh zero grid with 2 for six-cell components and 1
for all others. Diagonal contact does not merge objects.

## Exposure declaration

I had seen the assigned generator's intended rule before this post-repair solve,
so this is not a blind solve. During the solve lane I used only the displayed
examples and did not reopen the generator, Racket rule, reference code, private
labels, or prior solution explanations.
