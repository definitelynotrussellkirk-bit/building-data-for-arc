# Solve work log

## Exposure declaration

I had already inspected and repaired this task's generator and had seen the selected rule before this episode, so earlier exposure is `yes`. For this final-source solve I did not reopen the generator, Racket program, reference answers, private labels, or the retained prior solve. I used only the examples printed by `solve_episode.py prepare`.

## Revision 1 hypothesis

The top-right singleton is a color key. The color-1 connected component is a reference binary shape. Among the other monochrome connected components, exactly one is the same shape after a multiple of 90 degrees. The output is that component's tight bounding-box crop, with occupied cells recolored to the top-right key color and empty cells left 0.

Visible evidence:

- Example 0 maps a five-cell reference to the matching five-cell candidate and returns its 2x4 footprint in color 9.
- Example 1 refutes choosing the first candidate by location: the matching six-cell shape is lower-left and the result preserves its 4x3 footprint in color 3.
- Example 2 again selects by rotational shape equality, not by color, size alone, or proximity, and recolors the 3x3 crop with color 2.

The implementation removes the corner marker, finds four-connected monochrome objects, selects the largest color-1 reference, compares normalized crops under four rotations, and returns the first true match in reading order. Reflection is not needed by any visible pair.
