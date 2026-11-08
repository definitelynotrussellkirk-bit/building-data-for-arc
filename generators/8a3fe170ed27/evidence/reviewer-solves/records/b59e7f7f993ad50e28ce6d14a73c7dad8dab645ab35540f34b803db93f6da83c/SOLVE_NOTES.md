# Solve work log

I had no prior exposure to this task's rule, generator, private labels, or earlier solution explanations before this blind solve. I used only the visible examples produced by `python3 review.py blind prepare` and local tests against `challenge.json`.

## Hypothesis 1 — horizontal four-row wave

Each occupied row is shifted as a whole. Relative to the first occupied row, the offsets repeat every four rows as `[s, 0, -s, 0]`, with clipping at the grid edges. Examples 1–3 use `s = -1`; example 0 uses `s = +1`.

The visible distinction is the upper-left 2×2 cue: when the second occupied row also contains the cell immediately right of the object's leftmost column, choose `s = -1`; otherwise choose `s = +1`. Both test inputs contain that cue, so the predicted phase is `-1` for each. Remaining uncertainty: only one visible example demonstrates the `+1` phase, so another hidden cue could in principle select the phase.

I first added `test_solution.py`, which asserts the solver reproduces all four visible training outputs. Before implementation it failed at the template's `NotImplementedError`, confirming that the test exercises the missing behavior.
