# 4179e1ac3cf7

0-bg grid (h~9-14, w~11-16) with: (a) ONE MULTI-CELL COLOR-1 (blue) TEMPLATE — a 3-5 cell connected shape drawn from a shape bank, placed at random non-touching position; (b) 1-3 MATCHING COLOR-3 (green) COMPONENTS — each with the SAME normalized cell-set as the template (translated copies); (c) 0-2 DISTRACTOR COLOR-3 COMPONENTS with DIFFERENT normalized shapes. Matching components have enough room for their horizontal-mirror within their bbox + grid. Rule (OUTPUT FRESH GRID: FOR EACH MATCHING GREEN COMPONENT, PAINT THE UNION OF ITS CELLS + ITS LR-MIRROR IN COLOR 8; ERASE NON-MATCHING): identify the TEMPLATE (color-1) and its NORMALIZED SHAPE. PRODUCE a FRESH 0-grid. For EACH GREEN component matching the template: compute its bbox; PAINT its cells AND their LR-mirrored positions (within the same bbox) all in COLOR 8 (cyan). Distractor green components are DISCARDED. Net: matching shapes get their reflective twin in cyan; non-matching disappear.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
