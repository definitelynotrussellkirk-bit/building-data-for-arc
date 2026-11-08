# Solve notes — 65a142eb4d9b

This is a human-readable reasoning log written from `solve/challenge.json` only.
I had already seen the task rule while reviewing its generator, so this episode is
**exposed**, not blind. I did not consult the generator, Racket source, reference
solution, private labels, or earlier solve explanations after preparation.

## Visible-example observations

1. In training example 1, a lone color-3 cell becomes a five-cell cardinal plus.
2. In training example 2, lone colors 7 and 3 each become pluses, while the
   horizontally adjacent pair of color-3 cells at the bottom remains unchanged.
   Therefore expansion depends on same-color *cardinal* isolation, not merely on
   color frequency.
3. In training example 3, two color-4 cells touching only diagonally both expand.
   Their same-color pluses overlap harmlessly. The color-6 cell on the right edge
   also expands, but only into in-bounds cells, so edge arms are clipped.

## Hypothesis

Scan the original input. For each nonzero cell, test its up/down/left/right
neighbors in the original grid. If none has the same color, paint that center and
all in-bounds cardinal neighbors with its color in the output. Otherwise leave it
unchanged. Eligibility must not be recomputed from partially painted output.

## Expected test behavior

- Test 1: both separated cells (2 and 6) expand into independent pluses.
- Test 2: the vertical color-5 domino remains unchanged; the isolated color-5 at
  the upper-right expands despite sharing its color globally. Colors 6, 9, and 1
  also expand. This specifically checks local isolation rather than global color
  uniqueness.

No competing visible-example-consistent rule remained after checking the domino,
diagonal pair, repeated remote color, and boundary case, so I submitted one solve
revision.
