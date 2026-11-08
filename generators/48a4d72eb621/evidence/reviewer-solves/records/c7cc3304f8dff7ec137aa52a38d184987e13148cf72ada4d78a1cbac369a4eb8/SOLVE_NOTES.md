# Visible-only solve notes

This is a human work log written after `solve prepare`. I had earlier exposure to the task rule during the generator repair, so this is not a blind solve; during this solve phase I did not reopen the generator, Racket rule, reference solution, or private labels.

## Hypothesis

Each visible output contains exactly the multiset of nonzero input cells. Spatial position and adjacency are discarded, multiplicity is preserved, and values are sorted numerically ascending into one row.

Checks against the visible examples:
- Example 0 has counts 1×2, 3×3, 4×2, 5×1, 8×1, yielding `[1,1,3,3,3,4,4,5,8]`.
- Example 1 preserves all ten nonzero cells and sorts them.
- Example 2 preserves duplicate 3 and 5 values and the singleton 8.

The two visible queries therefore predict `[1,1,2,2,2]` and `[1,2,2,2,3,3,3,5]` respectively. The implementation directly flattens, filters zero, sorts, and wraps the result as one row.
