# Visible-only solve notes

This is a human work log. I had already reviewed the assigned generator and therefore mark earlier rule exposure as **yes**, but I did not consult the generator, Racket source, private labels, or reference solution during this solve episode.

## Hypothesis from the three visible examples

Every nonzero input cell acts as a center, regardless of its color. The output is a fresh zero grid of the same shape. For each center, paint its four orthogonal neighbors cyan (`8`) and omit the center itself. When halos touch or overlap, take their union.

Evidence from the examples:

- A lone `2` and a lone `9` both produce identical four-arm cyan crosses, so source color is irrelevant and output color is fixed.
- The two differently colored centers in the second example each contribute their cardinal neighbors; neither center is retained.
- Only orthogonal neighbors are painted, not diagonals.

I implemented this literal rule in one pass over the grid. No revision was needed before the first visible check.
