# Visible-only solve notes

This is a human reasoning log based only on `solve/challenge.json`. I had earlier exposure to the task while reviewing its generator, so this is an exposed post-repair solve. During this solve episode I did not consult the generator, Racket source, reference solutions, or private labels.

## Visible hypothesis

The input is four stacked 3-row masks. Corresponding cells are projected into one 3-row output. A nonzero value is selected by physical-band priority, not by its numeric color.

The visible pairs establish `band 0 > band 1 > band 3 > band 2`:

- Train 1 at projected `(0,1)`: band 1 has `4`, band 2 has `2`, band 3 has `8`; output is `4`, so band 1 beats bands 3 and 2.
- Train 1 at `(2,3)`: band 2 has `2` and band 3 is zero; output is `2`.
- Train 1 at `(2,5)`: only band 3 is nonzero (`8`); output is `8`.
- Train 2 at `(0,0)`: only band 2 is nonzero (`4`); output is `4`, while at `(0,1)` bands 1, 2, and 3 contain `8,4,2` and output is `8`.
- Train 3 changes the color assignment across physical bands, yet top-band `8` still wins at conflicts; this rules out a fixed color ranking.

Therefore each output coordinate scans bands `(0,1,3,2)` and copies the first nonzero cell, leaving zero only when all four are zero.

## Implementation

`solution.py` performs exactly that projected overlay after validating the 12-row rectangular input. The first implementation covers all visible training cells, so no speculative revision was added.
