# cfd3c4190aa0

0-bg grid (h, w~13-17) with: (a) CONTROL CELL at (0, 0) in color ∈ {1, 2, 3} encoding a BAND INDEX; (b) THREE NESTED COLOR-5 (gray) RECTANGULAR FRAMES drawn at offsets (0, 2, 4) from a centered anchor — outermost (frame 0), middle (frame 1, 2 cells inward), innermost (frame 2, 4 cells inward). Rule (CONTROL 1-3 SELECTS WHICH GRAY NESTED-FRAME BAND BECOMES CYAN): READ the CONTROL cell's color k ∈ {1, 2, 3}. The 3 nested frames define 3 BANDS: BAND-1 (ring between frame 0 and 1), BAND-2 (ring between 1 and 2), BAND-3 (interior inside frame 2). PAINT every bg-0 cell in the k-th BAND with COLOR 8 (cyan). Gray frames and control cell stay. Net: control color picks one nested ring to fill cyan. Flag: HARDCODED-LOW DIVERSITY — 3 controls × ~9 grid sizes → ~26 distinct.

Kind: `per_puzzle`. Imported version: `3.0.1`.
Approval is derived by the catalog from current code and retained evidence.
