# 99d5a207587c

0-bg grid (h ∈ 8-13, w ∈ 10-14, by difficulty) with: N ∈ 1-2 HOLLOW RECTANGULAR FRAMES, each fh × fw (fh, fw ∈ 4-5) drawn at non-overlapping positions via _free check, each in a DISTINCT FRAME_COLOR drawn from a 2N-color palette (so 4 distinct colors when N=2). INSIDE EACH FRAME: ONE SINGLE SEED CELL at a random interior position, painted in a SEED_COLOR (the OTHER half of the palette, distinct from the frame color). Rule (FOR EACH RECT-FRAME, FIND THE SINGLE NON-FRAME SEED INSIDE; FILL ALL OTHER 0-CELLS OF THE FRAME'S INTERIOR WITH THE SEED'S COLOR; FRAME OUTLINE AND SEED CELL PRESERVED): For EACH rect-frame: COMPUTE its INTERIOR (cells strictly inside the outline). READ the unique non-frame-color seed cell inside → seed_color. PAINT all 0 cells in the interior with seed_color. Outline stays frame_color. Net: each frame's interior floods with its seed's color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
