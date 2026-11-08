# Solve work log

I had not seen task `84def340ce03`, its generator, or its Racket rule before this episode. I used only the visible challenge prepared in `solve-blind/`.

## Observations and hypothesis

- Every output is square with side length equal to half the number of input cells: `4×6 -> 12×12`, `6×10 -> 30×30`, and `2×14 -> 14×14`.
- The square is partitioned into concentric rings. Each ring is split into four L-shaped corner segments (north-west, north-east, south-west, south-east).
- Flattening the even-numbered input rows gives the tape for the two upper corner segments. Flattening the odd-numbered rows gives the tape for the two lower corner segments.
- Consecutive pairs are consumed from the tapes from inside to outside. Equivalently, for ring depth `k` measured from the outside, its pair begins at tape index `n - 2 - 2k`.
- The left member of each pair colors the left corner-segment; the right member colors the right corner-segment. The top or bottom tape is selected by the output row's half.

A useful check was the `2×14` example: its central `2×2` block is exactly the first pair from each row, while the outer four corner-segments use the last pair from each row. The `4×6` and `6×10` examples confirmed that the tapes are formed by alternating rows rather than by splitting the flattened grid in half.

## Revision 1

Implemented the direct ring-index formula:

- `ring = min(r, c, n-1-r, n-1-c)`
- `pair_start = n - 2 - 2*ring`
- use the even-row tape above the horizontal midpoint, otherwise the odd-row tape
- use `pair_start` left of the vertical midpoint, otherwise `pair_start + 1`

Before implementation, a visible-example harness failed on the template's `NotImplementedError`, establishing the expected red test. After implementation, I reran the harness over all three visible examples and then used the episode checker.

## Remaining uncertainty

The examples all have an even number of rows and produce an even side length, which is required by the observed pair/ring construction. I assume generated queries obey that same domain. No reference source or private query labels were consulted.
