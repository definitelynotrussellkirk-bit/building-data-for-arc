# Post-repair visible-only solve — 7f03452e81df

This is a reviewer-authored work log, not a token-level model conversation.
Earlier rule exposure: yes, during the generator repair. Reference consultation
during this solve: no. After preparation I read only the public challenge and
its printed examples; I did not reopen the generator, canonical rule, earlier
solutions, private labels, or authoring helpers to construct this solution.

## Public observations

| Example | Input dimensions | Output dimensions | Distinguishing observation |
|---|---|---|---|
| 0 | 10 rows × 12 columns | 6 rows × 6 columns | The output rectangle retains an interior object of another color. |
| 1 | 10 rows × 12 columns | 2 rows × 3 columns | Equal four-cell candidates are resolved by the higher object. |
| 2 | 10 rows × 12 columns | 3 rows × 2 columns | Equal five-cell candidates with the same top row are resolved leftward. |
| 3 | 10 rows × 12 columns | 2 rows × 2 columns | A three-cell object wins over larger components. |
| 4 | 10 rows × 12 columns | 2 rows × 3 columns | A four-cell component wins despite its color occurring in another, larger component. |

Both query inputs are 8 rows × 10 columns; their outputs are unknown.

## First genuine revision

The candidate rule uses same-color four-neighbor connected components against
background zero. It chooses by cell count, then top row, then left column. It
returns the corresponding rectangle from the original grid, preserving all
cells within that rectangle. The implementation uses a fresh component search
and array slicing; no query labels or private reference evaluation are used.

The five labelled examples supply the component-selection, row tie, column tie,
and crop-versus-mask evidence. Earlier exposure is disclosed, so this is not an
unexposed test of discovering the rule. No intentional negative was created.

The official visible-only check completed successfully on 5/5 labelled examples.
I stopped after the first revision because every visible pair matches. The two
masked-query outcomes remain unknown until independent maintainer scoring.
