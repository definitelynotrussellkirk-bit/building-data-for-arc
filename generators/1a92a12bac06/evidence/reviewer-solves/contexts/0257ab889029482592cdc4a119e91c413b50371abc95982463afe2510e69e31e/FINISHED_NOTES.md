# Fresh visible-only solve notes

Earlier rule exposure: **yes**. The generator and rule family had been inspected during the repair stage before this solve episode was prepared. After `solve prepare`, I did not reopen generator source, rule files, private labels, prior solve notes, or reference outputs.

## Observations

- Every nonzero object is a vertical, contiguous bar of color 2.
- Shape and all 0 cells are preserved.
- Within each bar, a suffix at the bottom changes from 2 to 8.
- For bar lengths 4, 5, 6, 7, 8, 9, and 10, the changed counts are 2, 2, 3, 3, 4, 4, and 5 respectively: exactly `floor(length / 2)`.
- Thus an odd bar keeps its middle cell blue; the lower cells become azure.

## Hypothesis tested

For every maximal contiguous vertical run of 2s, copy the grid and recolor its bottom `floor(run_length / 2)` cells to 8. Treat separate runs independently if a column ever contains more than one.

The implementation is intentionally component-local rather than tied to absolute rows, whole-grid height, or the longest bar. It should reproduce all three visible training examples and determines both visible queries without consulting hidden outputs.
