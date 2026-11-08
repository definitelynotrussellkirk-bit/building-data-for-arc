# 18a3c532c9dc

Even-dim n×n grid (n ~6-12, both even) split into 4 QUADRANTS (TL, TR, BL, BR), each ~hh×hh (hh=n/2). Each quadrant has its own distinct color and sparse non-bg cells (various layouts). Rule: output is hh × hh. For each (r, c) in output: v = TL_cell(r,c); if BR is non-0 → override with BR; if BL is non-0 → override with BL; if TR is non-0 → override with TR. Priority: TR > BL > BR > TL. Net effect: overlay all 4 quadrants into a single hh×hh, with later-checked quadrants winning.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
