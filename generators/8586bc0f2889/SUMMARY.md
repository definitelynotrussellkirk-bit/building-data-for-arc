# 8586bc0f2889

0-bg grid (h ∈ 8-10, w ∈ 9-12) with: TARGET ∈ 2-4 ISOLATED SINGLETON MARKER CELLS placed at INTERIOR positions (rows 1..h-2, cols 1..w-2) so each marker's 3×3 footprint stays in-bounds. Markers use DISJOINT 3×3 FOOTPRINTS (footprint of one cannot overlap another's via reserved-set tracking). Each marker painted in a random color from {1..9}. Rule (FOR EACH NON-BG INTERIOR MARKER, STAMP A HOLLOW 3×3 RING (8 CELLS AROUND THE CENTER, EXCLUDING THE CENTER ITSELF) IN THE MARKER'S COLOR; THE CENTER CELL STAYS PAINTED — OR PER DEMOS BECOMES BG): For EACH marker at (r, c) with color k: PAINT the 8 neighboring cells (r-1..r+1, c-1..c+1) excluding (r, c) with color k. The center (r, c) keeps its original color (or is set to 0 per demos). Net: each marker becomes a hollow 3×3 colored ring; background outside footprints stays 0.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
