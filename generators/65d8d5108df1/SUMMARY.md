# 65d8d5108df1

0-bg grid (h~10-13, w~12-16) with: (a) LIBRARY REGION (rows 0..h-4) containing 3-4 TEMPLATE SHAPES drawn from an 8-shape bank (varied 4-5 cell shapes), each in a DISTINCT color from {1..9} (color = template ID); (b) BOTTOM 3 ROWS = COMMAND ROWS — row h-3: template IDs per column, row h-2: transform codes (1=id/2=cw90/3=180/4=ccw90/5=flip-lr), row h-1: output recolors. 2-4 command columns are non-zero. Rule (DECODE LIBRARY + TRANSFORM + RECOLOR GALLERY): For EACH NON-ZERO COMMAND COLUMN c: LOOK UP template by ID = g[h-3][c]. CROP template to bbox. APPLY transform per code g[h-2][c]. RECOLOR uniformly to g[h-1][c]. HSTACK all transformed pieces with 1-col gaps. EMIT horizontally packed output. Net: command rows drive a transform-recolor gallery from the top library.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
