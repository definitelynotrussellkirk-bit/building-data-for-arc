# Solve work log

I had not seen this task's rule, generator, solution, notes, or audit evidence before this blind attempt. I used only the visible examples produced by `blind prepare`.

## Revision 1

Hypothesis: the transformation is local and horizontal. Every exact `1,0,1` motif is completed by changing its center zero to `1`. Overlapping motifs therefore turn `1,0,1,0,1` into a solid five-cell run. Other spacings, adjacent pairs, vertical motifs, and motifs whose center is a nonzero color remain unchanged.

Evidence from the visible examples:

- The changed rows contain `1,0,1` or a chain of overlapping copies.
- A row with ones spaced three columns apart is unchanged.
- A visible `1,2,1` row is unchanged, so the rule does not overwrite a colored center.
- Training example 0 contains a vertical `1,0,1` in column 0 that remains unchanged, ruling out a direction-independent fill.

I implemented a copy-preserving scan of the original rows, filling only centers of exact horizontal `[1, 0, 1]` windows. Remaining uncertainty is limited to whether a longer alternating run should be treated globally; the local rule and the global alternating-run interpretation coincide on all visible examples and queries.
