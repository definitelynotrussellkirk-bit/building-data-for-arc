# b75f0b915b2b

0-bg grid (h, w~14-18) with: (a) ONE HOLLOW COLOR-5 (gray) RECTANGULAR FRAME (5-7 × 5-7) drawn at random interior position; (b) INSIDE the frame (with 1-cell buffer from walls), a TEMPLATE SHAPE (3-4 cells from a bank of 8 templates) painted in TEMPLATE_COLOR (random non-{0, 1, 5}); (c) OUTSIDE the frame, 2-5 BLUE (color-1) CANDIDATE SHAPES — at least one with normalized cells matching the template, and at least one with a different shape. Rule (MATCH TEMPLATE → RECOLOR CANDIDATES): identify the gray FRAME and TEMPLATE inside. NORMALIZE the template's cells. For EACH BLUE CANDIDATE outside the frame, NORMALIZE its cells and compare. If they MATCH the template's normalized pattern, RECOLOR the candidate to TEMPLATE_COLOR. Non-matching blue candidates stay color 1. Frame + template stay. Net: blue shapes matching the framed template get template's color; others stay blue.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
