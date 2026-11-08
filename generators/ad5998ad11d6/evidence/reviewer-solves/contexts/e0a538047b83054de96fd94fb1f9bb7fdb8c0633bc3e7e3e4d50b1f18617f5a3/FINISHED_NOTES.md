# Solve work log

## Exposure declaration before solving

I had not opened the Racket rule, generator implementation, reference solutions,
private labels, prior solution explanations, or either assigned repair/audit
source. I used only the prepared visible examples in `challenge.json` and a local
Python comparison against their visible outputs.

## Observations and hypothesis

All inputs contain background color 0 and wall/outline color 3. Outputs preserve
every 3 and replace only selected 0 cells with 4. The changed cells form holes
inside closed color-3 outlines: examples include a one-cell diamond, a two-cell
vertical cavity, and a larger rounded rectangle. Background zeros outside those
outlines remain unchanged.

Hypothesis: regard the 3 cells as barriers. Flood-fill zero cells reachable from
any grid-edge zero using four-neighbor moves. Those reachable cells are exterior
background; every remaining zero is enclosed and should become 4.

## Probe

I wrote a temporary Python probe that loaded `WORK/solve-blind/challenge.json`,
ran that boundary flood-fill, and compared the result cell-for-cell with each
visible training output. It matched examples 0, 1, and 2 exactly. No failed
revision preceded this one.

An eight-neighbor flood-fill was considered but rejected: diagonal gaps in the
outline should not let the exterior leak through when the examples use
orthogonally adjacent 3 cells to surround a zero. Four-neighbor background
connectivity explains every changed cell exactly.

## Implementation

`solution.py` copies the grid logically, finds all exterior zeros with a deque,
and emits 4 for zero cells not in the exterior set. It preserves all nonzero
colors and does not mutate the input.

## Remaining uncertainty

The visible data consistently supports four-neighbor enclosure. Hidden queries
could contain irregular or nested outlines, but the same connected-component
rule handles both. I did not inspect hidden outputs or any reference source.
