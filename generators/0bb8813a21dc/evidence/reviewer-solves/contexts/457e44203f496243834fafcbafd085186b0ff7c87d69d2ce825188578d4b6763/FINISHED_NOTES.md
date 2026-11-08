# Solve work log

## Exposure

Before this solve I had not opened the task's generator, Racket rule, private labels,
reference solution, prior solve notes, or the assigned repair generator. I used only
the visible examples printed by `python3 review.py blind prepare`.

## Hypothesis

Each row is processed independently. Zeros retain their locations. In every nonempty
row, every nonzero cell is recolored to the color of the **leftmost nonzero cell** in
that row. An all-zero row stays all zero, and dimensions are unchanged.

The tempting alternative "use the most frequent nonzero color" is ruled out by train
1 row 0 (`5,9,0,9,6,0`), whose output uses 5 rather than the twice-occurring 9, and
by train 2 row 0, whose output uses 6 rather than the twice-occurring 8. The leftmost
rule explains every row of all three training examples.

## Predicted queries

For query 0, row leaders are 4, none, 6, none, and 8. For query 1, row leaders are
none, 4, 7, and 6. The implementation preserves the zero mask and replaces each
row's nonzero values with its leader.

## Verification

I first ran an external local regression test against the untouched template and saw
the expected `NotImplementedError`. After implementation, that test covers two
training examples, query-0 prediction, all-zero rows, and non-mutation of the input.
The packet's visible-only checker is the authoritative solve-episode check.

Remaining uncertainty is limited to an unseen rule that coincides with leftmost color
on every visible row; the repeated mode-counterexamples make the direct row-leader
rule the simplest supported explanation.
