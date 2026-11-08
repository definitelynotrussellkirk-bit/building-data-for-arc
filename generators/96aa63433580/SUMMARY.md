# 96aa63433580

0-bg grid with N (2-5) distinct colors. Each color appears at exactly 2 cells positioned as OPPOSITE CORNERS of a rectangle (so the bbox of those 2 cells defines a rectangle with width and height both ≥3). Different colors' rectangles may overlap or nest. Rule: for each color c with ≥2 cells, compute the bbox of ALL cells of color c, draw the border (outline) of that bbox in color c on a fresh 0-grid. Colors with <2 cells are ignored. Output: only the rectangle border outlines appear, no interior fill.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
