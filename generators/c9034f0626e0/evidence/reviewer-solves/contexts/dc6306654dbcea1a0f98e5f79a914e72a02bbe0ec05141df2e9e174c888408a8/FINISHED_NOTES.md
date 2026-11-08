# Solve work log

## Prior exposure

I had already reviewed this task's generator and parity rule before this final-source solve episode, so this is **not blind**. I did not consult the Racket authority, generator source, private labels, reference solutions, or prior solution notes during this episode; I used the newly prepared visible challenge only.

## Visible-example inference

Each input has exactly one nonzero, non-gray marker. In every demonstration, only background-0 cells change. The changed cells use the marker color and share both the marker's row parity and column parity. Gray-5 cells remain fixed even when their coordinates have the matching parity, and zeros in the other three ordered parity classes remain zero.

The implementation therefore finds the unique non-0/non-5 marker and recolors exactly those 0-valued cells `(r, c)` satisfying `(r % 2, c % 2) == (marker_row % 2, marker_col % 2)`.

## Alternatives rejected from the visible pairs

- Row parity alone would change extra cells in the opposite column parity.
- Column parity alone would change extra cells in the opposite row parity.
- Checkerboard sum parity would merge two ordered parity classes and overfill.
- Filling all zeros would ignore the three preserved classes.
- Overwriting gray cells would contradict fixed gray blockers.

No code revision was needed after the initial visible-example hypothesis.
