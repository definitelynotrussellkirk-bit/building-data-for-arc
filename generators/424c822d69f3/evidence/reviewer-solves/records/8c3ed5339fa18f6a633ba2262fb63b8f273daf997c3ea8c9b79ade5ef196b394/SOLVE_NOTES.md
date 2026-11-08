# Solve work log

## Prior exposure declaration

Before this fresh visible-only episode I had already inspected and repaired the task's generator and executable authority. I therefore cannot claim an unexposed solve; I will finish the episode with `--earlier-exposure yes`. During this episode I did **not** reopen the generator, Racket rule, reference solutions, private labels, or prior solve notes. The implementation below was reconstructed from the visible grids in `README.md` / `challenge.json`.

## Revision 1

### Visible observations

- Every nonzero cell in row 0 is a colored one-cell marker.
- Every object below row 0 is a 4-connected rectangle of color 5.
- Outputs preserve marker cells and background cells, while replacing each whole color-5 object with one marker color.
- Train 1 rules out simply assigning marker colors from left to right: its rightmost object is recolored 6 even though it is the third object and there are three marker colors.
- Train 2 shows the same marker color can be reused by multiple objects.

### Hypothesis

For each color-5 connected component, compute the horizontal midpoint of its bounding box and recolor the component with the top-row marker whose column is nearest. For even widths I use the integer midpoint `(left + right) // 2`, i.e. the left of the two middle columns. The visible examples contain no equal-distance tie, so leftmost-marker tie-breaking is only a conservative deterministic fallback.

### Implementation

`solution.py` finds 4-connected components of 5, computes each component's bounding-box midpoint column, chooses the nearest nonzero/non-5 marker in row 0, and recolors only that component. It preserves the input shape and all other cells.

### Predicted query behavior

- Query 0: all three object midpoints are closest to the marker at column 9, color 7, so every 5 becomes 7.
- Query 1: all three object midpoints are closest to the marker at column 2, color 1, so every 5 becomes 1.

### Remaining uncertainty

The demonstrations do not define exact-distance ties. The generated visible queries do not appear to contain one, so this uncertainty should not affect the episode result.
