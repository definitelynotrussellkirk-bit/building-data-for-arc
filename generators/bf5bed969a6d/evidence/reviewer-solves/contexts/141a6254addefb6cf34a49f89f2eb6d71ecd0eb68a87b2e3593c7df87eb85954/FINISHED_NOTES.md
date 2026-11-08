# Solve work log

Earlier exposure before this blind episode: **no known exposure** to task `bf5bed969a6d` or its rule. I read only the packet instructions and the public challenge prepared by `solve_episode.py blind prepare`; I did not open any generator, Racket rule, reference solution, private label, or prior explanation.

## Revision 1 — frame-centered copies plus crossed-frame copy

Visible pattern: color 2 is a small binary glyph. Every other nonzero color outlines a rectangular frame, sometimes with border cells obscured by another frame. The output erases the color-2 glyph and redraws it in each frame's own color, centered in the frame interior. The non-overlapping examples establish this directly, including upper-left tie-breaking when an interior and glyph differ by one cell.

The first example has crossed 5 and 8 frames. Two ordinary centered copies are present, but there is also a third color-5 copy centered on the smaller frame's corner lying inside the larger frame; unlike ordinary interior copies, it overwrites crossed border cells. I therefore added a pairwise overlap rule: choose the smaller frame, locate its corner inside the other frame, and center another stamp there. The two hidden queries contain touching/overlapping frame bounds, so this is the material uncertainty; a plausible rival is to add no third copy when frames merely share a border.

Implementation probes: I compared every changed training cell against the inferred stamps. Ordinary copies write only background, explaining why the 5-frame interior copy does not overwrite an 8 border in example 0. The overlap copy writes on top, explaining both 8→5 changes. Frame bounds are recovered from each color's extrema so occluded border runs do not break detection.

Remaining uncertainty: the examples do not uniquely specify even-sized stamp anchoring at a shared border or whether zero-area border contact deserves the overlap copy. I use upper-left-biased centering consistently and treat any nonempty bounding-box intersection as overlap.

## Revision 2 — require a genuine two-dimensional crossing

The first program treated every nonempty frame-bounding-box intersection as a crossed-frame region. A direct visible comparison passed examples 0 and 1 but added an unwanted color-9 stamp in example 2, whose two frames share only one border row. The checker confirmed 2/3 visible examples.

Repair: emit the extra smaller-frame copy only when the outer frame boxes overlap by at least 2 rows **and** 2 columns. This keeps the genuine 2×2 crossing in example 0 and excludes one-dimensional shared-border contacts. Both hidden inputs also show one-dimensional contact, so the best-supported prediction is ordinary centered copies only for them.
