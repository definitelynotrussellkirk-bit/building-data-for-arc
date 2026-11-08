# Solve work log

## Prior exposure

Before this fresh solve I had already reviewed this packet's generator and its
Racket authority, so earlier rule exposure is **yes**. During the solve itself I
kept those files closed and used only `solve/challenge.json`, the visible grids,
and `solve_episode.py check` feedback. No private query labels or reference
solution were consulted.

## Revision 1

**Visible hypothesis.** Each input has one column filled entirely with gray `5`;
other isolated gray cells can be distractors. Start a blank grid of the same
shape. Reflect only blue `1` cells horizontally across the full-height gray
column, recolor retained reflected cells cyan `8`, drop reflected cells that
leave the canvas, and erase every original/input distractor.

**Evidence from the visible demonstrations.** Examples 0 and 4 show left-to-right
reflection, examples 2 and 3 show right-to-left reflection, example 1 clips the
right-side source where reflected columns would be negative, and every example
removes non-blue colors plus isolated extra gray cells. The divider is therefore
the unique all-gray column, not the canvas midpoint or any isolated gray cell.

**Implementation.** Locate the unique full-height `5` column. For each blue cell
at `(r, c)`, compute `c' = 2 * divider - c`; write `8` at `(r, c')` only when it
is in bounds. Leave every other output cell zero.

**Alternatives rejected.** Reflecting all nonzero colors contradicts the erased
colored distractors. Overlaying onto the input contradicts the blank outputs.
Reflecting around the canvas midpoint contradicts off-center dividers. Requiring
the whole shape to fit contradicts the partially clipped examples.

**Remaining uncertainty before check.** None material; both query inputs match
properties separately demonstrated in training.
