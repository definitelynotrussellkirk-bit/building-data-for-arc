# Solve work log

## Exposure statement

Before this solve I had not opened task `d8111f3f714d`'s generator, Racket rule,
reference solution, private labels, audit evidence, or any earlier solution
explanation. I used only the visible examples emitted by `blind prepare`.

## Revision 1 — aligned spine plus perpendicular branches

Observation: every input contains red (`2`) singleton points. Exactly one row or
column contains two red points. The output keeps every red point, colors the cells
between the aligned pair green (`3`) to form a spine, then connects each remaining
red point perpendicularly to that spine with green cells.

Evidence from the three visible examples:

- Example 0 has red endpoints at column 13, rows 1 and 14. The output fills that
  vertical interval and attaches the other two red points horizontally.
- Example 1 has red endpoints at row 6, columns 2 and 14. The output fills that
  horizontal interval and attaches the other three red points vertically.
- Example 2 again has a vertical spine at column 16 and horizontal attachments.

Implementation: locate all red points; find the repeated row or column; draw the
inclusive segment while preserving red cells; then draw one perpendicular segment
from every off-spine red point to the spine. I use a deterministic largest-group,
then longest-span selection only as a defensive tie-breaker; the visible task has a
unique aligned axis. Remaining uncertainty is limited to unseen malformed inputs
with multiple competing aligned groups, which the examples do not suggest.
