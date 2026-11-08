# a92bb76c10ef

0-bg grid (h~8-11, w~10-14) with OBJECTS of THREE FIXED COLORS (2, 3, 4): for each color c ∈ {2, 3, 4}, place counts[c] (1-5) INSTANCES at slot positions from a fixed slot list (sparse rows × sparse cols). Each instance is a single cell, with 35% probability extended to a 2-cell horizontal pair by painting the cell to its right. Counts per color are INDEPENDENT and may vary 1-5. Rule (COUNT OBJECTS OF COLORS 2, 3, 4 — EMIT GROUPED COLOR RUNS SEPARATED BY ZEROS): COUNT the number of 4-CONNECTED color-2 components → n2. Same for color-3 → n3 and color-4 → n4. PRODUCE a SINGLE-ROW OUTPUT: emit n2 cells of COLOR 2, then a bg-0 separator, then n3 cells of COLOR 3, then bg-0, then n4 cells of COLOR 4. Output length = n2 + n3 + n4 + 2 (the separators). Net: the input's scattered colored objects collapse into a single-row count encoding. Flagged intrinsic-low (uniq_out=20): bounded by 5³ count combinations.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
