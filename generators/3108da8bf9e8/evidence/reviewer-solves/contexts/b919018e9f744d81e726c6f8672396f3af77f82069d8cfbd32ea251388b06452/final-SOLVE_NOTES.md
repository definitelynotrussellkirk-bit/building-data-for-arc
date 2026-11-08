# Solve work log

## Exposure declaration before solving

I had already reviewed and edited this generator and had seen the intended rule in the earlier generator-work phase. This is therefore **not a blind solve**. During this fresh solve phase I did not reopen the generator, Racket authority, private labels, reference solutions, or the previous round's solution/notes. I used only `solve/challenge.json`, the generated template files, my own probe, and visible-only checker feedback.

## Visible structure and first hypothesis

All three training inputs are 11x11. Entirely zero rows and columns split each grid into a 3x3 macro-grid of 3x3 blocks. Each block contains only colors 1 and 2. The output has the same dividers and appears to move complete blocks without changing their internal cells.

Hypothesis: count color-1 cells in each block, sort whole blocks by that count, then place the smallest three left-to-right on the bottom macro-row, the next three on the middle row, and the largest three on the top row.

## Probe

I wrote `solve/probe_counts.py` and ran:

```sh
python3 solve/probe_counts.py
```

Observed input/output count sequences:

- Train 0: input `[4,0,2,5,6,7,9,1,8]`; output `[7,8,9,4,5,6,0,1,2]`
- Train 1: input `[8,0,9,4,3,7,2,6,5]`; output `[7,8,9,4,5,6,0,2,3]`
- Train 2: input `[7,1,9,4,2,3,6,5,8]`; output `[7,8,9,4,5,6,1,2,3]`

For every pair, the multiset of complete 3x3 textures was unchanged. This supports block movement rather than repainting and explains why one count can be absent while rank order remains well-defined.

## Revision 1

Implemented a structural solver that discovers occupied row/column runs around all-zero separators, extracts blocks, sorts by number of color-1 cells, and writes the blocks into bottom-to-top destination rows. It does not hard-code the exact separator indices, although it does rely on zero being the separator and 1 being the ranking color, both directly supported by all visible examples.

Remaining uncertainty before checking: a different feature perfectly correlated with the one-count in the three visible demonstrations could exist, but complete texture preservation and the varying block patterns make one-count the simplest consistent rule.
