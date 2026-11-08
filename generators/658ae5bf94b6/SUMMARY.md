# 658ae5bf94b6

0-bg grid (h, w = 2*pw + 1 with pw=3-5) split by a FULL-HEIGHT COLOR-9 (maroon) VERTICAL DIVIDER at col pw. LEFT PANEL (cols 0..pw-1) and RIGHT PANEL (cols pw+1..w-1) are each filled at ~40% density with random colors from {2, 3, 4, 5, 6} at DIFFERENT (non-identical) patterns. Rule (XOR OCCUPANCY MASKS): produce an OUTPUT GRID of size h × pw. For EACH cell at (r, c) in the output, check if input[r][c] (left side, non-zero) XOR input[r][pw+1+c] (right side, non-zero). If EXACTLY ONE is non-zero, set output to COLOR 2 (red). If both or neither, set 0. Net: output marks positions where left and right panel occupancies disagree.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
