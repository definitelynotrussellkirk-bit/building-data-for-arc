# Solve work log

This is a human work log based only on `solve/challenge.json` during the solve phase. I had already seen the task rule while reviewing the generator, so this is **not blind**; I did not consult the generator, Racket source, reference solution, or private query labels after preparation.

## Visible-example observations

1. The output keeps the same dimensions and preserves every existing nonzero cell.
2. A pair of equal nonzero cells on opposite corners of a 2×2 window is completed into a solid 2×2 square of that color.
3. Both diagonal orientations are active:
   - training example 1 completes an anti-diagonal 9 pair and a main-diagonal 1 pair;
   - training example 3 contains several completions in both orientations.
4. The two missing corners must both be zero in the **input**. In training example 2, the diagonal 7 pair at rows 2–3, columns 2–3 is not completed because the fourth corner contains 9.
5. Endpoint colors must match. In training example 4, the diagonal cells 6 and 1 near the upper left are not completed.
6. Axis-aligned adjacent equal cells do not by themselves trigger a completion; only opposite corners of a 2×2 window do.

## Hypothesis

Scan every 2×2 window of the original input. If its main diagonal is the same nonzero color and both anti-diagonal corners are zero, fill the anti-diagonal corners with that color. Otherwise, if its anti-diagonal is the same nonzero color and both main-diagonal corners are zero, fill the main-diagonal corners. All tests use the original input, while writes go to a copy, so newly painted cells cannot create cascading matches.

## Query expectations used as a manual sanity check

- Query 1 has two clean equal-color diagonal pairs (7 and 9), so each becomes a solid 2×2 block.
- Query 2 has a clean diagonal 5 pair whose other corners include an existing 1, so it stays unchanged. The diagonal 1 pair farther right has two empty opposite corners and should become a solid 2×2 block.

No alternate hypothesis remained consistent with all four visible demonstrations, so I implemented the direct local scan once rather than manufacturing a failed attempt.
