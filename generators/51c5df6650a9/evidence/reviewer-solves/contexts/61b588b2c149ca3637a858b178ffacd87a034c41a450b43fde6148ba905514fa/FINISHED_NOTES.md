# Post-repair visible-only solve notes

Earlier rule exposure: yes, because I repaired this generator before this solve. During this solve I used only the prepared visible examples and did not reopen the generator, Racket source, canonical records, or private labels.

## Hypothesis

The nonzero cells in the first row are an ordered legend. Each legend color has one 4-connected body object below the blank separator row. For each color, tightly crop that object and paste the crop into a new same-sized black grid, in legend order, beginning at row 1 and column 0. Leave one blank column between successive crops.

The examples distinguish legend order from body reading order: for example, train 0's body objects appear roughly as 6, 1, 2 spatially, while the legend requests 2, 6, 1 and the output follows 2, 6, 1. They also show that the crop preserves holes and shape, not merely the bounding rectangle.

## Implementation

`solution.py` reads unique nonzero top-row colors left-to-right, finds each color's body component by cardinal flood fill, computes its bounding box, translates occupied cells to output row 1 and the current horizontal offset, then advances by crop width plus one.
