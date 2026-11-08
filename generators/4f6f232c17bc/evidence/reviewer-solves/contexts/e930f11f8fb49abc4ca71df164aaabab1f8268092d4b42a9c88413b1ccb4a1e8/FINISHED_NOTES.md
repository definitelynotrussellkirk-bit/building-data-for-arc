# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, notes, reference solution,
audit records, or private query labels.  I used only the examples printed by
`python3 review.py blind prepare` and `WORK/solve-blind/challenge.json`.

## Hypothesis

Every input contains a complete gray (`5`) divider column and a blue (`1`)
object entirely on one side.  The output removes all input content and draws the
blue object reflected across the divider, recolored azure (`8`).  Reflection is
around the divider cells themselves, so for a vertical divider at column `d`,
source column `c` maps to `2*d-c`.  Reflected cells outside the original canvas
are clipped.

The other nonzero colors (`4`, `6`, `7`, or `9`) are distractors.  This is
supported by:

- train 0: columns 3/4 reflected around divider 5 become 7/6;
- train 1: columns 3/4/5 reflected around divider 2 become 1/0/-1, explaining
  the cropped rightmost part;
- train 2: only source column 4 survives at reflected column 10, while columns
  2 and 3 land beyond the width.

## Alternatives considered

I considered whether the isolated non-blue markers selected a direction or
translation distance.  They vary in count, color, side, and position without
matching the output.  The divider-centered reflection alone explains every
output cell and both clipping cases, so I did not give the markers a role.

## Implementation and probe

Before implementation, the visible-example harness failed on the supplied
`NotImplementedError`, establishing the red state.  I then implemented a
zero-background reflection of color `1` across the unique full color-`5` line,
painting color `8` and clipping out-of-bounds cells.  A horizontal-divider branch
is included as the axis-symmetric extension, though the visible examples only
establish the vertical case.

Remaining uncertainty is limited to unseen layouts that violate the visible
contract (for example, multiple full gray lines or a different object color).
