# Post-repair solve notes

This is an exposed solve: I had already reviewed the assigned generator, so earlier rule exposure is **yes**. During this solve I used only the visible examples in `README.md`; I did not reopen the generator, Racket source, canonical reference, private labels, or prior solve records.

## Hypothesis

Each input contains three nonzero 4-connected objects with different cell counts. The output preserves positions and background but recolors the largest object to 1, the middle-sized object to 4, and the smallest object to 2.

The second visible example is the useful discriminator: its five-cell elbow has a larger bounding box than the six-cell vertical line, yet the six-cell object receives 1 and the five-cell object receives 4. Therefore the ranking measure is cell count, not bounding-box area.

## Implementation

Find all nonzero 4-connected components, sort by descending number of cells, then paint them with `(1, 4, 2)`. Reject inputs outside the visible three-distinct-size domain rather than silently inventing tie behavior.
