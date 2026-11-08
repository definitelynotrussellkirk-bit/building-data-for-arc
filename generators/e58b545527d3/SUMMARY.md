# e58b545527d3

0-bg grid (h~7-9, w~11-13) with 1-2 HOLLOW RECTANGULAR COLOR-8 (cyan) FRAMES — each a rectangle outline of width × height 4-5 (interior is 0). EACH FRAME strictly CONTAINS EXACTLY ONE SEED CELL at a random INTERIOR position (inside the frame, not on the border) in a SEED COLOR distinct from 0 and 8. Frames are placed at non-touching positions (≥1-cell padding). Rule (FILL EACH ENCLOSED INTERIOR WITH ITS SEED'S COLOR): For EACH COLOR-8 FRAME: find the bg-0 cells strictly INSIDE the frame's border (the enclosed region NOT border-reachable). IDENTIFY the SEED — the lone non-0 non-8 cell inside the frame's interior; its color is C. PAINT every BG-0 cell in the interior with COLOR C. The frame border stays at 8. The seed stays at C. Net: each frame's interior becomes solid in the seed's color.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
