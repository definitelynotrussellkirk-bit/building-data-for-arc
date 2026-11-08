# 7d12467b91a3

0-bg grid (h~5-7, w = 2*panel_w + 1 with panel_w~5-7) with TWO EQUAL-SIZE PANELS separated by ONE FULL-HEIGHT COLOR-8 (cyan) DIVIDER column. LEFT PANEL (cols 0..panel_w-1) contains a BINARY MASK — 5-10 cells painted in COLOR 1 (blue), the rest 0 (the mask pattern). RIGHT PANEL (cols panel_w+1..2*panel_w) contains COLOR PAYLOAD — some cells painted in various non-{0, 1, 8} colors; some payload cells overlap mask positions, some don't. Rule: use the LEFT PANEL as a BINARY STENCIL. For each cell at (r, c) in the right panel, KEEP its color if the corresponding LEFT-PANEL cell at (r, c) is NON-ZERO (color 1, in mask); otherwise CLEAR it to 0. After masking, CROP the result to its non-zero content bbox. Output: the cropped masked right panel. Net: left mask selects which right-panel colors to keep; output is cropped, masked payload.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
