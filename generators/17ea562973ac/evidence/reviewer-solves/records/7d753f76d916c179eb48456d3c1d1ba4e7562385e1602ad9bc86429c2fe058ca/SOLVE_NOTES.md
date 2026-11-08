# Blind solve notes — 17ea562973ac

## Visible-only hypothesis

Each input has one nonzero color. The output discards the original foreground placement and draws the perimeter of the smallest axis-aligned rectangle containing all nonzero cells, using that color. Cells strictly inside the rectangle become zero.

Evidence:
- Example 0 has two opposite-corner cells and becomes the full-grid rectangle outline.
- Example 1's bounding box is rows 2–5 and columns 0–6. The input cell at (3,1) lies strictly inside and is erased, distinguishing replacement from merely adding border pixels.
- Example 2's bounding box is rows 0–7 and columns 2–8, matching the output.

The implementation computes the nonzero bounding box, initializes a zero grid of the same shape, and paints its four sides. It rejects multiple foreground colors because that case is unsupported by the visible examples.
