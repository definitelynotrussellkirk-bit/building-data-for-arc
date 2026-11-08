# Blind solve notes

Source exposure: visible examples only. I did not inspect any generator, canonical
rule, private answer, prior solution, audit, or repair-task source.

## Hypothesis

The all-9 columns divide the grid into equal mini-panels. The first two panels
use one common color and represent a base object followed by an expanded object.
Compute the coordinates added in panel 2 relative to panel 1, ignoring color.
Each later panel is a candidate mask. The output has one cell per candidate:
8 when the candidate is nonempty and all its occupied coordinates are among the
added coordinates; otherwise 0.

Evidence from the visible training examples:

- Example 0 adds `(0,0)` and `(3,2)`; exactly the first and fourth candidates
  are subsets of those coordinates, matching `[8,0,0,8]`.
- Example 1 adds `(0,0)`, `(1,1)`, `(2,1)`; the singleton `(2,1)` and the
  two-cell mask `{(0,0),(1,1)}` match, while candidates with any outside cell do
  not, matching `[8,0,0,0,8]`.
- Example 2 adds `(0,1)`, `(1,0)`, `(1,1)`; the singleton `(1,1)` and pair
  `{(0,1),(1,0)}` match, yielding `[8,0,0,0,0,8]`.

The implementation locates separator columns structurally, so panel height and
width may vary. Occupancy means nonzero within a panel; separator 9s are excluded
by splitting before mask extraction.

Predicted masked outputs (not checked against private labels):

- Query 0: `[[0,0,8,8]]`
- Query 1: `[[8,8,0,0]]`
