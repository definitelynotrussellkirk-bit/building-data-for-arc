# Solve notes

This is a human visible-example work log. I had earlier rule exposure during the required generator review, so this is not a blind solve; after `prepare` I did not reopen the generator, Racket rule, reference solution, or private labels.

## Visible observations

- Every input has one nonzero cell in row 0 and an all-zero separator row beneath it.
- The row-0 color varies independently of component position, size, and distance.
- In train 0 the marker is color 2 and the output is the tight crop of the upper-right color-2 component.
- In train 1 the marker is color 8 and the output is the tight crop of the upper-right color-8 component.
- In train 2 the marker is color 2 and the selected color-2 component is bottom-left, ruling out a fixed position.
- In train 3 the marker is color 2 and the selected color-2 component is upper-right; the crop preserves zeros inside its bounding box.

## Hypothesis

Treat the unique nonzero cell in row 0 as a color legend. Find the 4-connected body component of that color below the separator and return its tight bounding-box crop, preserving internal zeros.

## Predicted queries

- Query 0 marker color 8 selects the bottom-left component, predicting `[[8,0,0],[8,8,8],[8,8,0]]`.
- Query 1 marker color 2 selects the upper-right component, predicting `[[2,0,0],[2,2,2],[2,0,0]]`.

The implementation uses 4-connectivity and selects the top-left matching component if an unseen input contains more than one; visible examples contain one matching body component.
