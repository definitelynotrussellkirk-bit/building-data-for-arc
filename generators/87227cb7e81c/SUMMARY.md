# 87227cb7e81c

0-bg grid (h~8-12, w~9-13) with: (a) a SMALL TEMPLATE OBJECT (L-shape [(0,0), (1,0), (1,1)]) placed at the LEFT side (rows 1..h-4, cols 1..w//2-2) in a TEMPLATE_COLOR (random from {1..9} excluding 0 and 8); (b) ONE COLOR-8 (cyan) MARKER cell placed on the RIGHT side (cols w//2..w-2, well away from the template). Rule (STAMP TEMPLATE AT MARKER): identify the LARGEST non-8 object (the TEMPLATE) and its ANCHOR (top-left of its bbox). Identify the COLOR-8 MARKER cell at (mr, mc). STAMP the TEMPLATE at the marker — paint the template's cells at offsets from (mr, mc) in the TEMPLATE_COLOR. The original template stays. Net: 8-marker indicates where to place a copy of the template.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
