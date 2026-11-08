# a4580cf49290

0-bg grid (h~10-12, w~11-13) with: (a) KEY COLOR at (0, 0) — a single non-bg cell choosing which shape to operate on; (b) TRANSFORM CODE at (0, w-1) — a single cell with value ∈ {1, 2, 3, 4, 5} encoding 1=identity, 2=rotate-CW, 3=rotate-180, 4=rotate-CCW, 5=flip-LR; (c) 3 MULTI-CELL SHAPES placed at random positions in rows 2..h-1, each in a distinct non-bg color from a 3-color palette — EXACTLY ONE of those shapes uses the KEY COLOR from (0, 0). Shapes are 4-conn isolated. Rule: find the shape whose color matches the KEY color. CROP it to its bounding box. APPLY the TRANSFORM encoded by the code. Output: the small transformed crop, in the key color. Net: top-left key picks the shape, top-right code picks the dihedral op; output is the resulting transformed crop.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
