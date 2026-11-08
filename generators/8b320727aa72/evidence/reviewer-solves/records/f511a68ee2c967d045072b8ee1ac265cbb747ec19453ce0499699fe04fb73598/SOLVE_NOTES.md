# Blind solve notes — task 8b320727aa72

## Observation
Each 29×29 input is a 5×5 array of equal 5×5 tiles. Four full monochrome
rows and columns separate the tiles. Most copies of the tile are identical,
but a few cell positions disagree among copies.

## Hypothesis
The output is one representative 5×5 tile, except every coordinate whose
25 copies are not unanimous is replaced by color 1. Coordinates that are
unanimous retain their common color.

## Probe
I split all three visible training inputs at the full monochrome separator
rows/columns and compared the 25 values at every within-tile coordinate.
The resulting disagreement masks matched every output exactly, including
coordinates where more than one distinct non-separator color could have been
chosen. This also predicts the two test outputs without needing a majority or
an assumed background color.

## Implementation
Detect full monochrome rows and columns, form the non-separator intervals,
extract every rectangular tile, then emit 1 at non-unanimous coordinates and
the shared value otherwise.
