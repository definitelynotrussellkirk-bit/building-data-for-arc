# 58bdb4259aa2

0-bg SQUARE grid (n ∈ 7-14, h = w = n, by difficulty) with: N_CELLS ∈ 3-12 NON-ZERO CELLS in 1-4 DISTINCT COLORS drawn per PALETTE_KIND ∈ {warm / cool / broad / primary}, placed per POSITION_BIAS ∈ {scattered (random in upper half) / tight (top-left corner) / diagonal (main diagonal) / row_aligned (one row)}. Cells lie in the upper half of the grid so the rotated copies fit. The bbox center of the non-zero cells is at integer coordinates. Rule (COMPUTE THE BBOX CENTER OF ALL NON-ZERO CELLS; FOR EACH NON-ZERO CELL, PAINT IT AT 4 ROTATED POSITIONS — 0°, 90°, 180°, 270° — AROUND THE BBOX CENTER): COMPUTE bbox center (cr, cc). For EACH non-zero cell at (r, c) with color k: ROTATE (r - cr, c - cc) by 0°, 90°, 180°, 270° → 4 (dr, dc) offsets. PAINT cells (cr + dr_i, cc + dc_i) = k for i ∈ 0..3 (in-bounds). Original cells preserved (as the i=0 rotation). Net: input pattern is replicated by 4-fold rotational symmetry around the bbox center.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
