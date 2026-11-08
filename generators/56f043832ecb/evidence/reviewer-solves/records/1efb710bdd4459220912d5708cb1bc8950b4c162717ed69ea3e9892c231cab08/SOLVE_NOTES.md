# Solve work log

I had no earlier exposure to task `56f043832ecb` before this visible-only episode. I did not inspect any generator, Racket rule, canonical record, private label, audit evidence, or prior solution.

## Revision 1 — complete rectangular frames are filled

The visible examples distinguish complete from incomplete monochrome rectangular outlines:

- Example 0 contains two complete rectangular frames; both interiors become their frame color.
- Example 1 contains a complete color-6 frame and a color-3 outline whose right edge is missing one cell. Only the complete color-6 frame is filled.
- Example 2 contains a complete color-9 frame plus a disconnected color-9 singleton. The frame interior is filled and the singleton is preserved.

Hypothesis: split each nonzero color into 4-connected components. For each component, take its bounding box. If the box has a nonempty interior and every cell on the bounding-box perimeter has the component color, fill that interior with the same color. Otherwise leave the component and background unchanged.

Predicted query behavior:

- Query 0: both the color-2 frame (rows 0–5, columns 7–9) and the color-4 frame (rows 3–7, columns 2–4) are complete, so both interiors are filled.
- Query 1: the color-7 outline is missing its left-edge cell at `(5, 0)`, so it remains hollow; the complete color-3 frame at rows 3–9 and columns 5–8 is filled.

Implementation uses only the visible grid, 4-neighbor component discovery, and direct perimeter verification. Remaining uncertainty is limited to unseen cases with overlapping frames or nonzero material inside a closed frame; neither behavior is demonstrated.
