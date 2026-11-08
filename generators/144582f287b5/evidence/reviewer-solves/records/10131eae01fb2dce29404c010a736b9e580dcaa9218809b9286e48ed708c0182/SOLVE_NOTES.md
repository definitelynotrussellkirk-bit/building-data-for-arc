# Post-repair solve notes

## Exposure statement

I had already inspected and repaired this task's generator and canonical rule before this episode, so this is **not blind**. During this solve episode I did not reopen the generator, Racket source, reference outputs, private labels, or prior solution notes. The implementation below was checked only against the visible examples prepared in `solve/README.md`.

## Visible-example hypothesis

All three training examples preserve the input dimensions and emit exactly four nonzero cells at the output corners. Their values come from the fixed 2×2 block at zero-based rows 1–2 and columns 1–2, preserving orientation:

- input `(1,1)` → output top-left,
- input `(1,2)` → output top-right,
- input `(2,1)` → output bottom-left,
- input `(2,2)` → output bottom-right.

Every other output cell becomes zero. The repeated 2s in training example 1 and repeated 6s in training example 2 are distractors: only the four fixed source cells contribute.

## Predictions

For query 0 (7×5), the corner values should be `4, 3, 7, 2`.
For query 1 (4×4), the corner values should be `4, 9, 6, 7`.

## Implementation choice

`solve` validates a rectangular grid of at least 4×4, creates a same-shaped zero grid, and copies the four fixed source values to the four corners. There were no failed visible-example revisions in this episode.
