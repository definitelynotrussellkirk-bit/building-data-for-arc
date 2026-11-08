# Solve work log

This is a human-authored work log for the final hash-bound episode. I had already read the task rule and generator during the required review, so earlier rule exposure is **yes** and this is not claimed as a blind solve. After final preparation I used only `solve/challenge.json`, my own Python, and visible-only checker feedback. I did not consult the Racket source, generator implementation, reference solutions, private labels, or the archived pre-final solve.

## Revision 1 — prepared stub

I executed the supplied `NotImplementedError` stub as a deliberate red probe. It produced an execution error and passed `0/3` visible examples, as expected. It was not a candidate transformation.

## Visible-example observations

All outputs are exact rectangular crops copied from their inputs.

- In training example 1, the selected color-3 object is an eight-cell hollow 3x3 frame. Smaller color-2 and color-6 objects are ignored.
- In training example 2, the selected color-6 object is again the largest by occupied-cell count, not the earliest object or the object with the largest color total.
- Training example 3 is decisive. Two color-4 shapes touch only diagonally. The output is the lower eight-cell component's 4x3 crop; the upper seven-cell component is excluded. Therefore equal color does not merge objects, and diagonal adjacency does not count as connectivity. This rejects global-per-color aggregation and 8-neighbor connectivity.
- The third output is irregular rather than a hollow frame, so “choose a frame” is also false. The crop preserves internal zeros and indentation.

The simplest rule consistent with all visible pairs is: find nonzero same-color components under orthogonal four-neighbor connectivity; select the unique component with the most occupied cells; crop the original input to that component's bounding box.

## Revision 2 — component/crop implementation

Implemented breadth-first search over same-color 4-connected components, selection by cell count, and an original-grid bounding-box crop. A reading-order fallback is included only for deterministic behavior if an unseen tie occurs; the visible lesson presents a unique largest component.

Remaining uncertainty before checking was limited to unseen tie policy and empty-grid behavior. Neither is demonstrated, so the implementation preserves the input on an all-zero grid and otherwise follows the visible rule without adding a speculative transformation.
