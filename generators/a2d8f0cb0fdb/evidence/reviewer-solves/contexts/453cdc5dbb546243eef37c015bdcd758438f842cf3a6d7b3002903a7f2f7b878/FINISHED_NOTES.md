# Post-repair solve notes

This is an exposed solve: I had already inspected the repaired task while doing generator work. During this solve phase I used only `challenge.json` and the local Python solution/checker, and I did not reopen the generator, Racket rule, reference solution, or private labels.

## Visible-example observations

1. Every output has the same dimensions as its input and a fully black first row.
2. In each example, the first nonzero value in the input's first row supplies the output color: 4 in examples 1 and 2, and 7 in example 3.
3. Below the first row, exactly the input cells with value 1 receive that selected color.
4. Other nonzero body values disappear. Example 3 is decisive: body values 6 and 5 become 0 while the 1-cells become 7.
5. Example 2 has three header markers (4, 9, 6), so it distinguishes the first nonzero header value from the last or only header marker.

## Hypothesis

Find the first nonzero cell in row 0. Return an all-zero grid of the same shape, then paint each body cell whose input value is exactly 1 with that header color. Never copy the header or body distractors.

## Implementation and checks

The scaffold's `NotImplementedError` was executed first as a diagnostic failing check. I then implemented only the rule above, preserving input immutability and rejecting empty, ragged, or legend-free grids. The next check is a genuine solve attempt against all visible examples.
