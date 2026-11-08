# Solve notes

The single nonzero cell in row 0 names a color. In every training example,
the output is the tight bounding-box crop around all cells of that color in
the body below row 0. The crop is raw rather than recolored: training example
3 preserves the color-2 intruder inside the selected color-3 bounding box.

Predicted queries:

- Query 0: marker color 4 selects the T-shaped body object, yielding
  `[[4,4,4],[0,4,0]]`.
- Query 1: marker color 5 selects the hollow 2x3 body object, yielding
  `[[5,5,5],[5,0,5]]`.

Implementation validates a rectangular grid, one marker, and at least one
matching body cell, then returns the untouched inclusive slice.
