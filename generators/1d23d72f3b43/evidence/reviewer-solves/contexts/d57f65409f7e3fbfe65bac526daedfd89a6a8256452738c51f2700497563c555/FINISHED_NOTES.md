# Post-repair visible-only solve notes

This episode was prepared after I had repaired the assigned generator, so I had earlier exposure to the task rule. I did not consult the Racket source, generator source, reference solution, or private query labels during this solve phase.

From the three visible examples alone, every nonzero color occurs exactly twice. The two cells of a color are opposite diagonal corners of an axis-aligned rectangle, and the output fills that color's entire inclusive bounding rectangle while leaving all other cells unchanged. This accounts for every changed cell in all three demonstrations, including both diagonal orientations and skinny rectangles.

I implemented that single hypothesis directly: collect positions by nonzero color, and for each color with exactly two positions, paint rows min..max and columns min..max. No alternate hypothesis or failed revision was needed because the visible examples distinguish this from the main-diagonal-only shortcut.
