# 15d6a8756e63

Small grid (h~5-12, w~5-12) with several non-bg cells scattered across SOME columns (the ACTIVE columns — at least one is fully empty, at least one has a non-bg cell). No color-8 (cyan) appears in input. Rule: (1) TILE the input 2×2 so the output is (2h, 2w). (2) For each output column c whose underlying input column ((c mod w)) contains AT LEAST one non-bg cell, OVERLAY color 8 (cyan) into every output bg cell of that column. Output columns whose underlying input column is entirely bg stay all-0 in the output. Original non-bg cells are preserved in their tiled positions. Net: a 2×2 tile of the input where every active column is shaded cyan in its empty cells.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
