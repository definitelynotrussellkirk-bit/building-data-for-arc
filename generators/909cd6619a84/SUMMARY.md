# 909cd6619a84

h × w grid (small examples plus medium/large hard examples, up to 24×13) with bg = 7 (orange) and sparse non-7 cells in colors 5 and/or 9 (~25-55% density). Various layouts (scatter, blob, stripes, diag, frame, checker). Rule: rotate input 90° CCW → core. Output dimensions: (2*core_h + 3) × (core_w + 2). For each output cell (r, c): let period = core_h + 1. If r % period == 0 → it's a SEPARATOR ROW: cells at col 0 and col core_w+1 are 7, else 1. If r % period != 0 → it's a CORE ROW: cells at col 0 and col core_w+1 are 1 (side border), interior cells are core[r%period - 1][c-1]. Net effect: rotate-CCW the input, then frame in 1-border with 7-corners and tile vertically twice.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
