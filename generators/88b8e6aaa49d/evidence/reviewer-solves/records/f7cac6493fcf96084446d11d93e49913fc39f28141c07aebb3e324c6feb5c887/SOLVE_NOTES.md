# Solve work log

## Prior exposure

Before this visible-only episode I had already inspected the assigned generator and its selected rule while repairing it, so earlier rule exposure is **yes**. During this episode I did not reopen or consult the generator, Racket rule, reference solutions, private query labels, or the earlier blind-solve explanation.

## Revision 1 — execution error, not a rule test

I inferred a 180-degree rotation from the visible pairs, but my shell command wrote to `solve/solution.py` relative to the packet root instead of the actual `WORK/solve/solution.py`. The write failed, leaving the prepared `NotImplementedError` stub in place. The checker therefore recorded an execution error with 0/3 visible examples; this did not test or falsify the geometric hypothesis. I retained this genuine workflow mistake rather than rewriting history.

## Revision 2 — 180-degree rotation

All three visible examples keep the same dimensions and exactly preserve color counts. In example 1, the top-left `8` moves to bottom-right, top-right `5` moves to bottom-left, and bottom-left `6` moves to top-right. The other examples show the same coordinate map `(r, c) -> (H-1-r, W-1-c)`. This is a 180-degree rotation, equivalently reversing the row order and then reversing every row.

I implemented that rule directly for arbitrary rectangular grids. The competing one-step hypotheses (horizontal reflection, vertical reflection, transpose, or 90-degree rotation) fail visibly on example 1. Remaining uncertainty is only the masked-query score, which this workflow intentionally withholds; the visible examples leave no unresolved ambiguity among the basic geometric transforms.
