# 0d9784b230ca

0-bg grid (h~7-10, w~7-10) with ONE MARKER FRAME — three corners of an axis-aligned 2×2 local-coordinate system painted in fixed marker colors 5, 6, and 7 (origin at random non-degenerate position via choose_frame helper, basis vectors vx, vy each ±1). Specifically the markers sit at: ORIGIN (color 5), ORIGIN + vx (color 6), ORIGIN + vy (color 7). The FOURTH CORNER at ORIGIN + vx + vy is left 0 and is guaranteed in-bounds. All other cells are 0. Rule (CLOSE THE 2×2 MARKER FRAME): find the three marker cells (colors 5, 6, 7). INFER the local 2×2 coordinate frame: 5 = origin, 6 and 7 along orthogonal axes from origin. COMPUTE the missing fourth corner = origin + (6's offset) + (7's offset). PAINT that fourth corner with a designated FILL COLOR (e.g., the maximum of the three marker colors, or a fixed convention per demos). The three marker cells stay unchanged. Net: the partially-drawn 2×2 marker block is completed into a full 4-corner block with a new color in the previously-empty corner.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
