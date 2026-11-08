# 4c8a69defd74

Small 0-bg grid (h×w, h=3..5, w=3..5) with EXACTLY ONE MODE color (strictly most frequent, >50% of cells). Other cells use 1-3 minority colors. Rule: self-tile the input. Output is h*h × w*w. For each cell (r, c) in the input, if its value equals the mode, place the entire input grid at block (r*h..r*h+h-1, c*w..c*w+w-1) in the output; otherwise that block is all 0. Effect: input acts as both the unit tile AND the mask of where to place itself.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
