# Solve work log

## Exposure declaration before solving

I had not opened this task's generator, Racket rule, reference solution, private labels, audit records, or earlier solution explanations. I used only the visible examples emitted by `blind prepare` and the local visible-only checker.

## Revision 1 — diagnostic baseline

Command: `python3 review.py blind check --intent diagnostic_probe ...`

The untouched scaffold raised `NotImplementedError`, as expected. This established that the visible checker exercised the submitted `solve(grid)` rather than accepting an empty placeholder.

## Revision 2 — directional tile assembly

Observation: every input consists of nine isolated, filled 3×3 non-zero tiles. Each tile is mostly color 5. Eight tiles contain an accent shape and one tile is all 5. The output is a 3×3 arrangement of those 3×3 tiles, hence 9×9.

Hypothesis: the accent's displacement from the tile center selects the tile's output cell. A top-left accent goes in the output's top-left 3×3 block, a top-edge accent in top-middle, a left-edge accent in middle-left, and so on. The all-5 tile goes in the center. Accent color is payload, not an address: visible example 2 reuses color 2 for two differently shaped tiles, and they occupy different output positions.

Implementation: find 4-connected non-zero components, require each to be a filled 3×3 tile, sum each accent cell's signed row and column displacement from local center `(1, 1)`, quantize each sum by sign to top/middle/bottom and left/middle/right, and copy the whole tile into the corresponding output block. Reject duplicate or missing output positions instead of silently returning a partial grid.

Remaining uncertainty before checking: the visible examples strongly support exactly nine separated full 3×3 tiles and directional accents; no evidence shows touching tiles, variable tile sizes, or a background other than 0.

## Revision 3 — exact-cover tile extraction

Visible-check result for revision 2: execution failed before comparison because some valid 3×3 tiles touch orthogonally, so a non-zero connected component can contain more than one tile. The transformation hypothesis was not refuted; the extraction assumption was.

Repair: enumerate every all-non-zero 3×3 window and solve a small exact-cover problem over the 81 non-zero cells. This permits touching tiles while still requiring nine disjoint filled tiles. A visible-only probe over all three training inputs and both query inputs found exactly nine candidates and one complete cover in every case. The directional placement logic is unchanged.
