# Solve work log

Earlier rule exposure before this blind solve: none. I used only the visible
examples in `challenge.json` / `README.md` and local Python comparisons.

## Revision 1 — rectangular emitter with independently blocked rays

Across all three demonstrations, the unique color-8 component is a filled
rectangle. The output preserves that rectangle and extends color-4 rays from
all of its occupied rows to the left/right and from all of its occupied columns
up/down. Each row or column ray is independent. Cells colored 0 or 2 are
transparent and become 4; any other non-8 color is an opaque blocker, remains
unchanged, and prevents the ray from continuing beyond it.

Checks against the examples that distinguish this from a simple bounding-box
fill:

- Train 0: the upward ray in column 10 stops at the vertical color-5 object,
  while columns 11–13 continue to the top. The rightward ray in row 13 stops at
  color 6, but rows 11–12 continue to the edge.
- Train 1: color-2 rectangles intersecting the emitter's projected rows and
  columns are overwritten, while color-1 objects stop only the rays that meet
  them.
- Train 2: the color-9 object blocks columns 3–4 below the emitter, leaving
  columns 5–7 to continue; red/color-2 cells on projected rays are repainted.

Implementation finds the color-8 bounding rectangle, then walks four sets of
rays and applies those transparent/blocking rules. Remaining uncertainty: the
visible data always uses color 8 as the emitter and color 2 as the transparent
foreground, so the implementation intentionally follows those demonstrated
roles rather than guessing a more general color-selection rule.
