# Visible-only solve notes

The four displayed training pairs contain separated color-6 objects on a zero background. The output is one tightly cropped object rather than a composite.

Hypothesis from the first two pairs: count each 4-connected object's cells, rank the objects by area, select the middle-sized object, normalize its bounding box, and transpose it. Example 0 has three distinct object areas and returns the area-5 object transposed. Example 1 has five distinct object areas and returns the median one; this rules out always choosing a fixed position or the second-smallest object.

Examples 2 and 3 agree: the selected object's occupied-cell count equals the median area and the output dimensions are the selected bounding-box dimensions reversed. I therefore implemented 4-connectivity, area ranking, tight normalization, and matrix transposition. This is a fresh visible-example implementation, but I had already inspected the repair target's rule before this required post-repair solve, so earlier exposure must be recorded as yes.
