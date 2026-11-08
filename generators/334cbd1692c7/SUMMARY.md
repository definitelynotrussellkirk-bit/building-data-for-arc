# 334cbd1692c7

Variable-size 0-bg grid (14..30) with: (a) a large RECTANGLE (varied size) in some color (rect_color); (b) one MARKER cell of a different color at the rectangle's center; (c) outside the rectangle: a KEY shape — a marker-colored center cell with 4 ARM segments extending up/down/left/right (each arm is 2 cells of a distinct color: up-color, down-color, left-color, right-color). Rule: detect bg = most common color. Detect rect_color = most common non-bg. Find rectangle objects of that color. Compute marker_color from cells inside the rect that are neither bg nor rect_color (mode). Find OUTSIDE marker cells (same color, not in any rect). The one with most nearby non-bg neighbors = KEY CENTER. Grow the key region from the center via 8-conn non-bg cells outside rects. Then for every marker inside each rectangle, STAMP the key's offsets (relative to key center) at that marker's position, painted in the corresponding key arm colors.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
