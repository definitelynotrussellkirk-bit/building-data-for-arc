# Solve work log

## Exposure declaration

I had already inspected this task's generator and canonical rule while repairing it before this solve episode. During this episode I used only `solve/challenge.json`, my own probe, and the visible feedback from `solve_episode.py check`; I did not reopen the generator, Racket rule, references, private labels, or the previous solution explanation.

## Visible-example analysis

The grids contain nine equal 3×3 tiles separated by complete zero rows and columns. Input and output preserve each tile exactly but change tile positions.

I wrote `solve/probe_counts.py` to compare tile identities and simple statistics using only the three visible train pairs. In every pair:

- the nine tiles have distinct counts of color `1`;
- output tile rows contain the high, middle, and low thirds respectively;
- within each output tile row, counts increase from left to right.

Equivalently, sort all tiles by their count of color `1`, then place them left-to-right beginning with the bottom tile row and proceeding upward. The three visible output count sequences were:

- `[6,8,9] / [3,4,5] / [0,1,2]`
- `[7,8,9] / [3,4,5] / [0,1,2]`
- `[7,8,9] / [4,5,6] / [0,1,3]`

These observations reject fixed positional permutations and row-local sorting because the source indices differ across examples and output rows contain tiles drawn across input rows.

## Revision 1

Implemented dynamic detection of all-zero separator rows and columns, extraction of equal-sized tiles, global sorting by color-1 count, and placement from the bottom macro-row upward while preserving separators. Remaining uncertainty is limited to unseen tie behavior; no visible example contains a tie, so Python's stable sort supplies deterministic behavior without inventing a secondary key.
