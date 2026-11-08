# 974fee515740

0-bg grid (h~10-14, w~12-17) with: (a) TWO CONTROL CODES at row 0 — g[0][0] is the OP-CODE from {3, 4, 6, 7} (AND/OR/XOR/NOT) and g[0][1] is the ROTATION-CODE from {1, 2, 3, 4} (0°/90°/180°/270°); (b) RED SHAPE — a 5-cell plus (PLUS_5) painted at (3, 1) in COLOR 2; (c) BLUE SHAPE — a 4-cell L-shape {(0,0),(0,1),(1,1),(2,1)} painted at (4, w-5) in COLOR 1. Rule (ROTATE BLUE BY CODE, APPLY OP WITH RED, RENDER AS MINIMAL CYAN GRID): READ OP-CODE op and ROTATION-CODE rot. ROTATE the blue mask by rot * 90°. APPLY boolean operation (AND / OR / XOR) between rotated blue mask and the red mask. CROP the resulting boolean MASK to its BBOX. OUTPUT is a MINIMAL GRID with each on-cell painted COLOR 8 (cyan). Net: control codes drive a rotation + bool-op between the two shapes; output is their combined mask. Flag: INTRINSIC-LOW DIVERSITY — small minimal cyan crop yields ~12 distinct outputs.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
