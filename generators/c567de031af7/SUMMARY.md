# c567de031af7

FIXED-SIZE 15×15 grid divided into 9 sub-grids of 5×5 each (arranged 3×3). BG = bg_color drawn from {1..9} (non-zero) — the entire grid starts filled with bg. N_ZERO_SUBS ∈ 1-7 RANDOMLY-CHOSEN sub-grids (out of 9) each get N_PER_SUB ∈ 1-4 ZERO CELLS placed per ZERO_POSITIONS_KIND ∈ {scattered (random), cluster (Manhattan around random center), border (perimeter), diagonal (main diag), single (one random)}. Rule (OUTPUT A 3×3 GRID WHERE EACH CELL (SR, SC) IS 0 IF THE CORRESPONDING 5×5 SUB-GRID AT rows SR*5..SR*5+4, cols SC*5..SC*5+4 CONTAINS ANY 0; OTHERWISE THE CELL IS BG_COLOR): DETERMINE bg_color = g[0][0]. PRODUCE a 3×3 output. For sub (sr, sc) in 0..2 × 0..2: SCAN cells in rows sr*5..sr*5+4, cols sc*5..sc*5+4; IF any cell is 0: OUTPUT[sr][sc] = 0; ELSE: bg_color. Net: 15×15 summarized to 3×3 zero-presence matrix in bg color.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
