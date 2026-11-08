# Solve work log

I had no earlier exposure to this task's rule, generator, reference solution, private labels, or prior solve notes. I used only the visible examples prepared in this directory.

## Revision 1

Hypothesis: full rows/columns of color 9 partition the grid into equal square tiles. In every tile, color 2 is the shape and the final shape color is 8. A tile containing one or more color-3 cells is marked for exactly one 90-degree clockwise rotation of its color-2 pattern; the marker cells themselves disappear. An unmarked tile keeps the shape in place. Marker count and marker position do not affect the rotation.

Probes from the visible pairs:

- Train 1 middle tile: `(0,0),(0,1),(1,2)` becomes `(0,2),(1,2),(2,1)`, exactly a clockwise quarter-turn.
- Train 2 left tile gives the same mapping with a marker in a different position.
- Train 4 bottom-left 4x4 tile has two markers but still rotates only once, so presence rather than count is the control.
- All unmarked tiles preserve their 2-cell coordinates and merely recolor them to 8.

Implementation: detect complete 9 separator rows and columns; process each non-separator tile independently; collect only color-2 coordinates; rotate them clockwise when any 3 occurs in the tile; write the result as color 8 while retaining separators. The visible tiles are square, which is necessary for a quarter-turn to preserve the output dimensions. Remaining uncertainty is whether unseen lawful inputs ever contain non-square tiles; the examples consistently support square tiles.
