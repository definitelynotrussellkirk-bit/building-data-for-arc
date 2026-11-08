# 6ce8f4377282

Fixed 9×11 grid with COLOR-8 (cyan) WALLS forming a 2×2 COMPARTMENT LAYOUT: rows 0, 4, 8 are fully 8; cols 0, 5, 10 are fully 8. This creates 4 INTERIOR COMPARTMENTS at (1..3, 1..4), (1..3, 6..9), (5..7, 1..4), (5..7, 6..9). EACH COMPARTMENT contains 1-2 SAME-COLOR MARKER cells in a DISTINCT color from {1, 2, 3, 4, 5, 6, 7, 9} (different across compartments). Rule (FILL EACH COMPARTMENT WITH ITS MARKER COLOR): For EACH COMPARTMENT (4-conn non-8 region bounded by 8-walls): identify the MAJORITY non-0, non-8 COLOR (the marker color). REPAINT all 0-cells in that compartment with the marker color. The 8-walls stay. Net: each compartment fills with its marker's color.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
