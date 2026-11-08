# 1c1ef857c9e2

Grid (h ∈ 9-20, w ∈ 9-20, by difficulty) entirely PAINTED with BG_COLOR (any non-0 color drawn from {1..9}), divided by: (a) N_SEP_ROWS ∈ 1-3 FULL ROWS of SEP_COLOR (a distinct non-bg color); (b) N_SEP_COLS ∈ 1-3 FULL COLS of sep_color. Sep rows + cols placed per position_bias ∈ {evenly_spaced / centered / edge_heavy / alternating / scattered}. Sep cells overwrite bg, forming a grid of bg-colored bands. Rule (DETECT BG VS SEP, COUNT FULL SEP ROWS AND COLS, OUTPUT IS A (S_ROWS+1) × (S_COLS+1) GRID FILLED WITH BG_COLOR): IDENTIFY bg_color = the most-common color in the input. IDENTIFY sep_color = the non-bg color that appears as full rows/cols. COUNT s_rows = number of full-sep rows; s_cols = number of full-sep cols. PRODUCE a fresh (s_rows + 1) × (s_cols + 1) GRID filled entirely with BG_COLOR. Net: the input's sep-row × sep-col grid structure becomes a small (bands+1)² counting matrix; colors collapse to bg only.

Kind: `per_puzzle`. Imported version: `2.4.0`.
Approval is derived by the catalog from current code and retained evidence.
