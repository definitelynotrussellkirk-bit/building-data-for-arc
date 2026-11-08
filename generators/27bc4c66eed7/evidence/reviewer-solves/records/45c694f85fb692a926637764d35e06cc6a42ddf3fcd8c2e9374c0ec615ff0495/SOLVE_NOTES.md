# Solve notes

This is a human work log based only on `solve/challenge.json`. I had already reviewed the assigned generator before this exposed solve, so earlier rule exposure is **yes**; I did not consult the Racket rule or any reference solution during this solve.

## Hypothesis

Each maximal horizontal run of one nonzero color is compressed independently to a single cell of the same color on an otherwise-zero grid. The retained cell is at `start + floor(length / 2)`, so odd runs keep their center and even runs keep the right of the two middle cells.

Evidence from the five visible examples:

- Length 5 at columns 0..4 becomes column 2.
- Length 3 at columns 1..3 becomes column 2.
- Length 2 at columns 1..2 becomes column 2, confirming the right-middle convention.
- Two separated runs of color 9 on one row are handled independently, including a singleton that remains in place.
- Runs sharing a row do not interact.

No competing interpretation fits the even-run example as directly. I will implement a row scan that identifies maximal equal-color nonzero runs and writes one midpoint per run to a fresh zero grid.
