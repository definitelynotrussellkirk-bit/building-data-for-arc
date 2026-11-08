# 6b4c9de41354

0-bg grid (h, w ~ 8-18) with 4-CONNECTED OBJECTS in 2 categories: (a) BORDER OBJECTS — 1-3 components placed at the GRID BORDER (touching row 0, row h-1, col 0, or col w-1), shapes drawn from a 6-shape bank (L_tromino / rect_2x2 / single / line / L_5cell / blob); (b) INTERIOR OBJECTS — 1-3 components placed strictly INTERIOR (not touching any border), same shape bank, placed via place_no_overlap with 1-cell margin. Each object painted in a DISTINCT non-{0, 2, 8} color drawn from a 3-5 color palette. Rule (RECOLOR BY BORDER-TOUCHING STATUS — BORDER OBJECTS → COLOR 2, INTERIOR OBJECTS → COLOR 8): for EACH 4-CONNECTED non-bg COMPONENT: CHECK if any cell of the component lies on the grid BORDER (row 0, row h-1, col 0, or col w-1). IF YES: RECOLOR every cell of the component to COLOR 2 (red). IF NO (fully interior): RECOLOR to COLOR 8 (cyan). Net: border objects unify in red; interior objects unify in cyan; topology of which objects touch the border emerges visually.

Kind: `per_puzzle`. Imported version: `2.1.0`.
Approval is derived by the catalog from current code and retained evidence.
