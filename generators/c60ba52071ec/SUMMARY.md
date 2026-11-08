# c60ba52071ec

Fixed 8×26 0-bg grid with: (a) 2 FULL-HEIGHT COLOR-5 (gray) DIVIDER COLUMNS at col 8 and col 17, splitting the grid into 3 PANELS of width 8 each; (b) TWO PANELS each contain a 3-COMPONENT CONTACT CHAIN (3 2×2 blocks at (3, 1), (3, 3), (3, 5)) — degree pattern [1, 1, 2]; (c) ONE PANEL (odd_panel ∈ 0..2) contains a 4-COMPONENT CHAIN drawn from 3 hardcoded shapes — degree pattern [1, 1, 2, 2]. Each panel uses 4 distinct colors from {1..9}\{0, 5}. Output uniq_out=3 (intrinsic — 3 odd chain shapes, output recolored to 8). Rule (FIND ODD PANEL BY DEGREE MULTISET, CROP & RECOLOR TO 8): identify the 3 PANELS (separated by 5-divs). For EACH PANEL, compute the contact-chain DEGREE MULTISET. Find the ODD panel (unique degree multiset). EMIT the ODD panel's cluster cropped and RECOLORED uniformly to COLOR 8. Net: odd-out panel's shape, in cyan.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
