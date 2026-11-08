# Fresh solve notes

This is a human work log, not a token-level model trace. I had earlier exposure
to the task rule during generator review, but after `solve_episode.py prepare` I
kept the generator, Racket source, reference solutions, prior explanations, and
private labels closed. The implementation below was checked against the visible
examples only.

## Visible-example observations

- Every output has twice the input height and twice the input width.
- Nonblank input content appears unchanged in the top-left block and again in
  the bottom-right block. The other two blocks remain zero.
- A blank source row can instead become a full row of color 3 across the entire
  doubled width, and the same row is repeated one input-height lower.
- Train example 2 establishes that a *leading* blank row becomes 3, so the rule
  is not merely “blank rows strictly between colored rows.”
- Train example 3 has a trailing blank row after the last nonblank row; it stays
  zero in both vertical halves. Thus the separator condition is: blank and at or
  before the last nonblank source row.
- Train example 4 contains two qualifying blank rows and both are painted,
  ruling out “first blank only.”

## Revision 1

Hypothesis: create a `2h x 2w` zero canvas; copy each ordinary source row into
the top-left and bottom-right blocks; replace every all-zero source row whose
index is no greater than the final nonblank row with color 3 across both output
halves.

Implementation: `solve/solution.py`. It handles rectangular inputs and an
all-blank grid defensively (`last_nonblank = -1`, so no separator is painted).
No deliberate teaching negative or failed implementation was used before the
first visible check.

## Visible check result and stopping reason

Revision 1 executed successfully and matched all 4/4 visible training outputs.
I stopped because the visible controls jointly determine the implementation I
used: leading blank, internal blank, multiple blanks, trailing blank, rectangular
shape, multicolor copying, and blank off-diagonal blocks are all represented.
Masked test correctness remains withheld for independent scoring.
