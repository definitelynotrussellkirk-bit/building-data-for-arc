# Solve work log

This is a human-authored work log. I had reviewed this task's generator and rule before this fresh solve, so earlier rule exposure is **yes**. During the solve phase I consulted only `solve/challenge.json`, wrote the Python program here, and used `solve_episode.py check`; I did not consult the generator, Racket source, canonical source, private labels, prior solve artifacts, or reference solutions.

## Revision 1

**Visible evidence.** Each example contains several separated same-color 4-connected objects. The output preserves every object's exact cropped shape and color, top-aligns the crops, and inserts one zero column between them. The left-to-right order follows occupied-cell count: for example, the first training pair orders the one-cell color-3 object, the two-cell color-4 domino, then the three-cell color-2 object. The larger demonstrations continue that ordering even when scan position, color, bounding dimensions, and morphology differ.

**Hypothesis.** Find each nonzero same-color 4-connected component; crop it to its own bounding box; sort crops by exact number of occupied cells ascending; top-align and concatenate them with one zero separator column.

**Implementation.** `solution.py` uses an explicit 4-neighbor flood fill, derives each crop from min/max row and column, sorts by `(cell_count, color)` (the visible examples have distinct counts, so color is only deterministic fallback), and constructs the packed output.

**Probe planned.** Run the visible-only checker once. A pass on all four demonstrations is sufficient to stop because the rule accounts for every preserved cell, output dimension, gutter, and ordering choice in the visible data. The two query labels remain masked.

**Remaining uncertainty before checking.** The visible examples do not require a tie policy for equal-size objects. The generated lesson appears to use distinct object sizes; the implementation nevertheless uses color as a deterministic fallback.
