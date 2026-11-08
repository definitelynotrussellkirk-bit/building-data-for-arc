# Visible-only solve log

The three demonstrations share one transformation:

- preserve rows 0 and 1 exactly;
- treat row 0 as an **ordered sequence of positions**, not a set of unique colors;
- for each row `r >= 2`, fill the whole row with `input[0][(r - 2) % width]`.

Evidence:

- Train 0 cycles `6,1,2,4` twice through rows 2–9.
- Train 1 overwrites the existing 9-colored rectangle, so the operation is replacement rather than fill-only.
- Train 2 uses repeated header values `5,8,8,5,8,5`; the output follows those positions exactly, ruling out a deduplicated-color cycle.

I implemented that single hypothesis directly. I had seen the abstract rule earlier during generator review, so this is an exposed post-repair solve, not a blind solve; I did not consult the Racket source or private labels during this solve phase.
