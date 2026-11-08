# Solve work log

## Prior exposure

Before this solve I had already reviewed this task's generator and canonical rule as part of the assigned repair, so this is an **exposed** solve rather than a blind one. During the solve itself I did not reopen the generator, Racket rule, reference solutions, private labels, or prior solution explanations. I used only the visible challenge presentation.

## Revision 1

Hypothesis: treat each nonzero color as one or more **4-connected** components, choose the component with the greatest number of cells, and return the original grid restricted to that component's tight rectangular bounding box. Background zeros inside that rectangle remain in the output.

Evidence from the visible examples:

- Example 0 selects the seven-cell color-6 component, not either four-cell square.
- Example 1 selects the seven-cell connected color-8 component even though the disconnected color-3 cells total ten.
- Example 2 selects the six-cell color-7 component rather than aggregating the two color-6 squares (eight cells total).
- Example 3 selects the seven-cell connected color-9 component rather than aggregating the two color-1 components (ten cells total).

This rules out global color frequency and supports component size. The varying output dimensions are exactly the selected component's bounding box, including internal zeros.

Predicted queries before running the checker:

- Query 0: the six-cell color-3 component at the lower left; expected crop `[[0,3,3],[3,3,3],[3,0,0]]`.
- Query 1: the seven-cell color-3 component on the right; expected crop `[[3,0,0,0],[3,3,3,0],[0,0,3,0],[0,0,3,3]]`.

Implementation: flood-fill same-color orthogonal neighbors, retain every component, select the largest, then crop the input to its min/max row and column. Remaining uncertainty is only behavior on ties or an all-background grid; neither occurs in the visible examples. The implementation returns the unchanged grid for an all-background input and uses scan-order tie breaking via Python's `max`, but those are defensive choices outside the demonstrated domain.
