# fa9566ca9637

0-bg grid (h~8-11, w~9-12) with: (a) ONE CONNECTED COLOR-3 (green) BLOB of 2-4 cells (the PROTOTYPE) at a random interior position; (b) 1-3 SINGLE COLOR-1 (blue) ANCHOR cells placed so that stamping the PROTOTYPE (with anchor as top-left of stamp's bbox) stays in-bounds and doesn't overlap existing non-0 cells. Rule (STAMP PROTOTYPE IN COLOR 3 AT EACH 1-ANCHOR): identify the 3-BLOB PROTOTYPE (its normalized cell offsets). For EACH 1-ANCHOR at (ar, ac), STAMP the prototype's cells in COLOR 3 with (ar, ac) as the bbox top-left. EMIT a clean 0-grid with only the stamps (and the original prototype, or output may drop it). Net: each blue anchor sprouts a copy of the green prototype shape.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
