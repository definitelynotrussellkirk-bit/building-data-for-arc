# Blind solve notes — 083ba0fc4534

I used only the visible examples in `challenge.json` / `README.md`.

## Observation

Every input is three equal-width grids separated by full-height columns of color
5.  The output has the same height and the width of one panel.

At each output coordinate, compare the three aligned cells:

- `(0, 9, 9) -> 9`
- `(7, 0, 7) -> 7`
- `(3, 3, 0) -> 3`
- `(0, 7, 9) -> 0`
- `(9, 0, 1) -> 0`

This is a cellwise majority vote.  A color is retained when at least two of the
three panels agree; with three different values there is no majority and the
output is 0.  Zero naturally wins when it appears twice.

## Implementation

`solution.py` locates full-height color-5 separator columns, splits the input
into exactly three equal-width panels, and applies the majority rule at every
coordinate.  The checks for rectangular input and panel structure are defensive;
they do not alter the visible-task rule.
