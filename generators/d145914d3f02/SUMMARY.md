# d145914d3f02

0-bg grid (h~11-14, w~12-15) with: (a) ONE COLOR-9 (maroon) ORIGIN cell at interior position (nine_r, nine_c) (within rows 2-4, cols 2-4); (b) 2-3 COLOR-7 (orange) CELLS placed at fixed OFFSETS from the origin (one of 4 templates: small L-shapes / corners). These define the TEMPLATE; (c) 1-3 single ANCHOR cells with values from {2, 3, 4, 5} (the rotation codes: 2=0°, 3=90°, 4=180°, 5=270°), placed at scattered interior positions with sufficient margin from the origin and each other so rotated stamps stay in-bounds. Rule: extract the TEMPLATE as the color-7 offsets relative to the COLOR-9 origin. For EACH ANCHOR cell with rotation code v, ROTATE the template's offsets by v's rotation (2=0°, 3=cw90°, 4=180°, 5=ccw90°), then STAMP COLOR-7 cells at (anchor + rotated_offset) positions. The anchor stays, the origin stays, and original templates stay. Net: each rotation anchor pulls a rotated copy of the template into its position in orange.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
