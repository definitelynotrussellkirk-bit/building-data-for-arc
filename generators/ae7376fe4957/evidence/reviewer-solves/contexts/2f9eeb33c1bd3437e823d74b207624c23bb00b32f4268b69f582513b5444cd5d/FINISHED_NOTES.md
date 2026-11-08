# Solve work log

This is a human work log from the visible examples. I had earlier exposure to the task rule while reviewing the generator, but I did not consult the generator, Racket source, reference outputs, or private query labels during this solve episode.

The visible examples support one consistent operation:

1. Locate the unique blue cell (color 1).
2. Scan row-major for red cells (color 2); the first red cell is the destination marker.
3. Translate every other nonzero cell by destination minus source. Later red cells are payload, not additional destinations.
4. Discard translated cells outside the original canvas.
5. Tight-crop the surviving translated cells.

Example 0 makes clipping visible: moving the payload from blue at `(8,3)` to red at `(2,9)` sends the rightmost payload column outside the 12-column canvas, and the surviving crop matches the 3×2 output. Example 1 distinguishes the row-major first red from later red cells and preserves later reds as payload. I implemented the rule directly and stopped after the first coherent revision if all visible examples passed.
