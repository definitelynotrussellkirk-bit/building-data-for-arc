# a1fffe30b85b

Small H × W binary grid (bg=0 + 1 fg color, H, W ≤ 9). Rule: self-tile — produce H² × W² output. For block at (br, bc) in [0, H) × [0, W): if input[br][bc] is fg, copy input into that block; if input[br][bc] is bg, leave that block all 0. The input thus serves as both a mask and a template.

Kind: `per_puzzle`. Imported version: `1.3.0`.
Approval is derived by the catalog from current code and retained evidence.
