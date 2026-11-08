# 85782e8a5dc9

0-bg grid (h = panel_size, w = 3*panel_size + 2) with 3 PANELS separated by BLANK (0) COLUMNS, each panel a panel_size×panel_size COLOR-5 (gray) RECT-OUTLINE FRAME with interior of size isize×isize (isize~3-4). Interior pattern of each panel has 4-6 cells in colors {1, 2, 3, 4}: PANEL A has random PATTERN_A, PANEL B = TRANSFORM_T(PATTERN_A) where T ∈ {identity, rot90, rot180, transpose, flip_lr, flip_ud, cmirror}, PANEL C has random PATTERN_C (unrelated). Rule (SOLVE A:B::C:? ANALOGY): identify the 3 PANELS' INTERIORS. INFER the TRANSFORM T such that B = T(A). APPLY T to C's INTERIOR. EMIT the transformed C (or full output with C interior replaced). Net: A:B::C:T(C) analogy applied to the C panel.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
