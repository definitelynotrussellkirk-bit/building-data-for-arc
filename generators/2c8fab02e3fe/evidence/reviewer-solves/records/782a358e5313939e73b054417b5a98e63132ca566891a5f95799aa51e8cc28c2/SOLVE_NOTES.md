# Solve work log

## Prior exposure

I had not opened this task's generator, Racket rule, reference solution, private
query labels, audit records, or earlier solution notes. I used only the visible
examples printed by `python3 review.py blind prepare` and `challenge.json`.

## Revision 1 — singleton color fills the framed interior

Observed a complete rectangular border made from color 8 in every example. The
output leaves that border and all cells outside it unchanged, but replaces every
strictly interior cell with one color.

Hypothesis: among colors other than background 0 and frame color 8, the color
that occurs exactly once in the whole input is the instruction color. Fill the
strict interior of the 8-border rectangle with that singleton color, replacing
any interior distractors.

Evidence from the visible pairs:

- Example 0: singleton 5 fills the 3×3 interior.
- Example 1: singleton 1 fills the interior; the two 5 cells are distractors.
- Example 2: singleton 7 fills the interior and replaces the two interior 9s.

Alternatives considered and rejected:

- Nearest colored cell to the frame: example 1 has adjacent 5 cells, yet color 1
  is used.
- A color located outside rather than inside: example 2 includes 9 only inside,
  but singleton frequency, not mere location, distinguishes 7 from 9.
- Preserve nonzero interior cells while filling zeros: example 2 replaces both
  9 cells, so the whole interior must be overwritten.

I first added a visible-pair regression test and confirmed it failed against the
provided `NotImplementedError`. The implementation then locates the 8-cell
bounding rectangle, finds the sole non-0/non-8 singleton color, and fills the
strict interior. Remaining uncertainty: the visible data do not define behavior
for malformed frames or multiple singleton colors; the solution conservatively
returns the input unchanged in those unsupported cases.
