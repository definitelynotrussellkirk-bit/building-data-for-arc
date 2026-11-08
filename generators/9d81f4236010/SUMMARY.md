# 9d81f4236010

Grid where the MODE color is the background (often 2, sometimes 5 or 0). The most-frequent non-bg color is the FRAME color. The grid contains 2-4 solid frame-color rectangular blocks at non-touching positions. Each block has 1-3 marker cells inside in OTHER colors (replacing frame-color cells). The frames may have different sizes; the largest determines the output bbox. Rule: output is sized to the LARGEST frame's bbox; start filled with frame_color. For each frame, overlay each marker at local coords (r-r0, c-c0) within the output canvas. Markers from different frames may be at different local coords; they merge onto the shared canvas.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
