# 277c2478bab6

0-bg grid (h, w~13-17) with: (a) CONTROL CELL at (0, 0) in COLOR ∈ {2, 3, 4} encoding a band index; (b) THREE CONCENTRIC COLOR-1 (blue) FRAMES drawn at offsets (0, 2, 4) from a centered anchor — frame 0 outermost, frame 1 middle, frame 2 innermost. Rule (A CONTROL COLOR SELECTS ONE OF THREE BLUE NESTED-FRAME REGIONS FOR BLANK-OUTPUT FILL): READ the CONTROL cell's color k ∈ {2, 3, 4}. The 3 concentric blue frames define 3 BANDS/REGIONS: region-1 = ring between frame 0 and 1; region-2 = ring between 1 and 2; region-3 = interior inside frame 2. SELECT the k-th REGION. PRODUCE a FRESH BLANK 0-grid and PAINT only that region with the control color k. Net: control color picks one nested ring; output is that ring on a blank canvas in the control color.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
