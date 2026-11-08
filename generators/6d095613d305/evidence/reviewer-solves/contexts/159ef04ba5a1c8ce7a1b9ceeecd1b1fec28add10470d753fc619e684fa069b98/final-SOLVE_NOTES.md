# Fresh solve notes for 6d095613d305

This is a human work log written from `solve/challenge.json` only. It is not a
captured model conversation and contains no token-level traces or probabilities.
I had seen the task rule earlier while reviewing the assigned generator, so this
attempt is **not blind**; during this solve phase I did not reopen the generator,
Racket authority, canonical ledger, private labels, or prior solution text.

## Visible-example observations

- Every input contains isolated markers in two nonzero colors; every output has
  orthogonal colored paths on the same-size zero background.
- In training example 1, the color-2 markers occur at `(0,7)`, `(5,4)`, and
  `(6,6)`. The output goes left along row 0, down column 4, right along row 5,
  then down column 6. This supports row-major marker order and a
  horizontal-before-vertical bend for each consecutive pair.
- The color-5 markers in that example similarly form one horizontal-first bend
  followed by a vertical segment. Their path shares `(0,4)` with color 2, and
  that cell becomes 9.
- Training example 2 supplies several shared cells; all become 9, while repeated
  occupancy by only one color remains that color. This rejects simple
  last-color overwrite at inter-color intersections.
- Training example 3 has four markers for one color, showing that all consecutive
  waypoints are used rather than connecting only the first and last markers.

## Considered alternatives

1. **Vertical-first bends.** Rejected by example 1: it would descend from
   `(0,7)` before moving left, unlike the visible row-0 segment.
2. **Column-major marker ordering.** Rejected by the visible chains in examples
   1 and 2, whose turns follow increasing row order.
3. **Connect every marker directly to a hub or just first-to-last.** Rejected by
   intermediate turns that pass through each marker in examples 1 and 3.
4. **Paint overlaps with whichever path is drawn last.** Rejected by the 9 cells
   in examples 1 and 2.

## Chosen algorithm

For every nonzero input color, collect and row-major-sort its marker coordinates.
Build that color's occupied-cell set by including the first marker and, for every
consecutive pair, walking horizontally on the first point's row to the second
column and then vertically on that column to the second row. Finally paint a
fresh zero grid: a cell used by exactly one color receives that color; a cell
used by two or more different colors receives 9.
