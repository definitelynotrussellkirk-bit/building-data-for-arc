# 23e6fb027242

0-bg grid (h~8-10, w~9-11) with: (a) ROW 0 contains 1-2 distinct CODE cells in {1, 2, 3, 4} at random columns — encoding a border SIGNATURE (1=top edge, 2=right edge, 3=bottom edge, 4=left edge); (b) ROWS 1+ contain 2-3 BODY rectangular components in distinct colors, exactly ONE of which has a bbox that touches PRECISELY the set of borders named in the code. Rule: read codes (sorted set). Find the body component whose border-touch signature matches the code set exactly. Crop it to its bbox and UPSCALE by 2× (each cell → 2×2 block). Output: that 2× scaled crop.

Kind: `per_puzzle`. Imported version: `2.3.0`.
Approval is derived by the catalog from current code and retained evidence.
