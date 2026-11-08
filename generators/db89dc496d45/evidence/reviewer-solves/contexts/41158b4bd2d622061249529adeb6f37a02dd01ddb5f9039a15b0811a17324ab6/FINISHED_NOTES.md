# Solve work log

## Prior exposure

Before this fresh solve I had already inspected the task's rule and generator while repairing the assigned package, so **earlier rule exposure is yes**. During this solve episode I did not reopen or consult the Racket rule, generator implementation, private labels, reference outputs, or prior solve notes. I used only the newly prepared `solve/challenge.json` / `solve/README.md` visible examples.

## Revision 1

Hypothesis: treat each nonzero color as one or more separate objects under four-neighbor connectivity, select the object with the greatest cell count, and return that object's tight bounding-box crop with all non-object positions left as background zero.

Evidence from the visible pairs:

- Example 0 selects the five-cell color-3 component, not all six color-3 cells and not the five total color-9 cells split across two components.
- Example 1 selects the six-cell color-7 component even though color 4 has seven cells globally split into components of three and four.
- Example 2 selects the seven-cell color-2 component while excluding its isolated eighth color-2 cell; it beats the four-cell color-9 component despite seven color-9 cells globally.
- Example 3 selects the eight-cell connected color-6 shape while color 5 has nine cells globally split into components of five and four.

These examples rule out “most frequent nonzero color,” “crop all cells of one color,” and “second-most-frequent color when the top color is disconnected.” The implementation flood-fills equal-color cells with orthogonal neighbors, keeps the largest component, and emits only its cells inside a tight crop.

Remaining uncertainty: the visible examples contain no exact tie between largest components and no all-background input. The code resolves ties by row-major first occurrence and returns an empty grid for an all-background input; neither choice affects the shown lesson.
