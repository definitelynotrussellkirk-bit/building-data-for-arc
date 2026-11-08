# 0c58baa79ba5

0-bg grid (h~8-11, w~9-13) with EXACTLY TWO separated 4-connected objects, each a RANDOM polyomino (3-5 cells) of a DISTINCT normalized shape, in distinct non-bg colours (8 reserved for the rule output). Rule (XOR OF THE TWO NORMALIZED SHAPES): sort objects by reading order, take the first two, normalize each to its bbox top-left, output a max(bbox_h)*max(bbox_w) grid painted 8 where EXACTLY ONE shape is filled (symmetric difference), 0 elsewhere. Varied shape pairs -> varied cyan XOR masks.

Kind: `per_puzzle`. Imported version: `3.2.0`.
Approval is derived by the catalog from current code and retained evidence.
