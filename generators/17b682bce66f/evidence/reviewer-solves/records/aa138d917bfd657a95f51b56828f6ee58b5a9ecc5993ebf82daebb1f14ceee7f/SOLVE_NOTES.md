# Solve work log

I had no earlier exposure to this task's Racket rule, generator, private labels,
or solution explanation. I used only the visible examples printed by
`python3 review.py blind prepare` and the public `challenge.json`.

## Revision 1 — rotated stencil hypothesis

The input contains one connected stencil made of color 8 around a single color
9, plus isolated marker cells colored 2 through 5. I treated the 9 cell as the
stencil origin and represented every 8 cell by its relative offset from 9.

Visible example 2 makes the rotation code explicit. Around marker 2, the stencil
appears unchanged and is recolored 4. Around marker 3 it is rotated 90 degrees
clockwise and recolored 5; marker 4 gives 180 degrees and color 6; marker 5 gives
270 degrees and color 7. The marker itself remains its original color.

Examples 0 and 1 additionally show overlap and clipping. I simulated all three
stamps in example 0. Processing markers in ascending color means higher-color
stamps overwrite lower-color stamped cells, matching the observed 5-over-4 and
7-over-5 overlaps. Original marker cells must be protected: the color-5 marker
in example 0 occupies a location that the color-2 stencil would otherwise paint.
Cells outside the grid are simply omitted, as shown near the right edge in
example 1.

Implementation: locate the unique 9, collect all 8 offsets, keep isolated colors
2–5 as protected markers, rotate offsets by `(marker_color - 2)` quarter-turns,
paint with `marker_color + 2`, clip to bounds, and preserve all marker cells.
Remaining uncertainty before checking: whether there can be repeated markers of
the same color. The implementation supports that case deterministically.
