# Solve work log

Earlier exposure before this episode: yes. I had already inspected and repaired
this task's generator and canonical rule as required by the assignment. During
this solve episode I did not reopen those sources or consult private query
labels, reference solutions, or prior solution notes. I used only the four
visible demonstrations in `challenge.json` and the solve checker.

## Revision 1 — reflect painted cells across the complete color-5 axis

Hypothesis from the visible examples: a full row or full column of color 5 is a
mirror axis. Every nonzero, non-5 cell is copied to its coordinate reflected
across that axis, while the original cell and its color are preserved. The
operation applies independently to disconnected cells and to every source
color. Cells whose reflection would fall outside the grid are ignored, although
the visible examples keep all reflections in bounds.

Evidence from the demonstrations:

- Example 0 mirrors a connected color-2 shape from left to right across a
  vertical axis.
- Example 1 mirrors five disconnected/connected color-3 cells from above to
  below across a horizontal axis.
- Example 2 mirrors a multicolor, partly disconnected pattern from right to
  left across an off-center vertical axis, ruling out monochrome-only and
  component-only shortcuts.
- Example 3 mirrors two colors from below to above across an off-center
  horizontal axis, ruling out a fixed source-side shortcut.

Implementation: find the complete color-5 row; if none exists, find the
complete color-5 column. Copy every original nonzero, non-5 cell to the exact
reflection coordinate. Remaining uncertainty: the examples contain exactly one
complete color-5 axis, so the implementation deliberately does not invent a
policy for ambiguous multiple-axis inputs.
