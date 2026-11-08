# Solve work log

## Exposure and source discipline

I had not opened the task's generator, canonical rule, reference solution, private
query labels, audit records, or earlier solve explanations. I used only the public
presentation produced by `review.py blind prepare`, `challenge.json`, and my own
local visible-example test.

## Initial observations

Every visible input contains sparse nonzero markers on a zero background.

- In training example 0, the two 3s share a row and the output fills the inclusive
  horizontal segment. The two 7s and two 5s each share a column and their inclusive
  vertical segments are filled.
- Training example 1 repeats the same behavior with one horizontal and one vertical
  pair.
- Training example 2 has a horizontal 1 pair crossing a vertical 4 pair. The
  intersection is 4, so the vertical segment has precedence at crossings.
- Training example 3 is useful negative evidence: the two 2s are diagonal and are
  not connected, while color 6 occurs three times on one row and is also not
  connected. Thus the operation applies to colors occurring **exactly twice**, and
  only when their two cells are axis-aligned.

## Hypothesis

For each nonzero color that occurs exactly twice:

1. If its cells share a row, fill the inclusive horizontal interval with that color.
2. If its cells share a column, fill the inclusive vertical interval with that color.
3. Otherwise leave it unchanged.

Leave colors with multiplicity other than two unchanged. Draw horizontal intervals
before vertical intervals so vertical colors overwrite horizontal colors at a
crossing, matching training example 2.

## Test-first probe

I wrote `/tmp/test_blind_solution_184044.py` to import `solution.py` and compare its
result with all four public training outputs. Before implementation it failed at the
stub's `NotImplementedError`, confirming the probe exercised the missing solver.

## Query implications before checking

- Query 0 should extend color 1 vertically in column 0, color 8 vertically in
  column 4, and color 9 horizontally in row 5. At `(5, 4)`, vertical color 8 should
  overwrite horizontal color 9.
- Query 1 should extend color 3 vertically in column 2 and color 4 horizontally in
  row 2. At `(2, 2)`, vertical color 3 should overwrite horizontal color 4. This is
  a useful reversal of the training example's color ordering and supports an
  orientation-based, not numeric-color-based, precedence rule.

## Remaining uncertainty

The examples establish vertical-over-horizontal precedence for one crossing but do
not show coincident collinear segments of different colors; with exactly two points
per color, such overlap is possible in principle. The implementation follows the
smallest rule supported by the visible evidence and does not add special handling
for unobserved overlap cases.

## Revision 1 result and corrected crossing hypothesis

The first implementation drew all horizontal segments before all vertical segments.
The visible-example test failed on training example 1 at `(5, 3)`: it produced
vertical color 1, while the expected cell is horizontal color 2. This falsified
orientation-based precedence.

Comparing both crossing examples gives a simpler consistent rule:

- Example 1 crosses colors 1 and 2; color 2 remains.
- Example 2 crosses colors 1 and 4; color 4 remains.

Thus the larger numeric color wins at a crossing. I revised the renderer to process
qualifying colors in ascending numeric order, independent of segment orientation,
so later/higher colors overwrite earlier/lower colors. Under this corrected rule,
query 0's `(5, 4)` crossing should be color 9 (over 8), and query 1's `(2, 2)`
crossing should be color 4 (over 3).
