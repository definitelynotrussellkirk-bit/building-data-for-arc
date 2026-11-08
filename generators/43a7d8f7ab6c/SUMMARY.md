# 43a7d8f7ab6c

0-bg grid (h~8-12, w~9-14) with 1-3 ONE-CELL-THICK RECTANGULAR FRAMES (border outlines) in DISTINCT colors from {1..9}. Each FRAME has height 3-5 and width 3-6, with a non-empty INTERIOR (at least 1 bg cell inside the border). Frames are placed at non-touching positions (1-cell padding). Rule (FILL EACH HOLLOW RECTANGULAR FRAME INTO A SOLID RECTANGLE): For EACH CONNECTED COMPONENT that is a HOLLOW RECTANGULAR FRAME of color C with bbox (r0, c0, r1, c1): PAINT every cell at rows r0..r1, cols c0..c1 (the entire rectangle including border and interior) with color C. Net: each hollow rectangle becomes a solid rect of the same color.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
