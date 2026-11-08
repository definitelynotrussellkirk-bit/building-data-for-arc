# Post-repair visible-example solve notes

This is a human work log from the exposed post-repair episode. I had already
seen the task rule while reviewing the generator, so this is not a blind solve;
I nevertheless used only `solve/challenge.json` during this solve phase and did
not consult the generator, Racket source, private labels, or reference outputs.

## Hypothesis

Each input is a three-row strip of 3x3 tiles separated by all-9 columns. The
separator columns stay fixed, while whole tiles move. Counting nonzero cells in
each tile explains every training output:

- Training 1 has occupancies 5, 3, 2 and outputs them as 2, 3, 5.
- Training 2 has occupancies 6, 5, 3 and outputs them as 3, 5, 6.
- Training 3 has occupancies 4, 2, 1 and outputs them as 1, 2, 4.

The colors inside a tile and the tile's internal geometry are preserved, so the
candidate rule is: split at separator columns, sort complete tiles by increasing
number of nonzero cells, and reassemble with color-9 separators.

## Implementation

`solution.py` implements that rule directly and validates the three-row strip
shape. No alternate hypothesis was needed because the first rule matches all
three visible training pairs exactly and uses the same invariant across mixed-
palette and monochrome examples.
