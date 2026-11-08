# Post-repair visible-only solve notes

This is a human work log. I had earlier rule exposure from reviewing the assigned generator, so this is not a blind solve; during this solve phase I consulted only `solve/challenge.json`.

## Visible pattern

All three demonstrations erase the original scene, paint color 4 at every even column of the top row, and preserve exactly one original colored cell one row below the top at the same column. The preserved color is the first nonzero cell in row-major order:

- 8 precedes the later 5 in training example 1, so 8 survives at row 1.
- the lone 8 survives in training example 2.
- 9 precedes the later 3 in training example 3, so 9 survives at row 1.

The later nonzero cells are distractors. This distinguishes the rule from choosing the last nonzero seed.

## Implementation

Scan row-major for the first nonzero value, create a zero grid, paint the alternating top-row color-4 rail at columns 0, 2, 4, ..., and place the selected seed at row 1 in its original column. For a one-row defensive edge case, place it on row 0 after painting the rail; no visible instance uses that case.

## Predicted tests

- Test 1: alternating 4s across width 5; move color 9 from top column 2 to row 1 column 2.
- Test 2: alternating 4s across width 11; keep color 1 from top column 6 at row 1 column 6; discard the later color 2 at row 4 column 2.
