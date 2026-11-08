# b87adf923da8

0-bg grid (h~8-11, w~9-12) with: (a) one PROTOTYPE — one color-8 (cyan) ANCHOR cell adjacent to (or inside) a small RANDOM CONNECTED POLYOMINO (2-7 cells) painted in 1-3 varied non-{0,1,8} colors; (b) 1-4 single color-1 (blue) TARGET cells scattered apart from the prototype, each with room around them for a full stamp. Rule: find the anchor (the 8 cell). Targets = all color-1 cells. Offsets = for every non-{0, 1, 8} cell in the input, compute (r - anchor_r, c - anchor_c, value). For each target, stamp those offsets at the target's position (target becomes new 'anchor'), each cell painted with the original value. Output: a fresh empty grid with all stamped cells. The original prototype, anchor, and target markers all DISAPPEAR in the output.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
