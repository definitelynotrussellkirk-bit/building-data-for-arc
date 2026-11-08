# eca9d989b5bd

0-bg grid (h~5-7, w~6-8) with 1-5 COLORED MARKER CELLS placed ONLY in the BOTTOM ROW (h-1) at DISTINCT random columns, each in a DISTINCT non-zero color from 1..9. The rest of the grid (rows 0..h-2) is entirely 0. Rule (UP-LEFT DIAGONAL RAY): for EACH BOTTOM-ROW MARKER at (h-1, c) with color C, EMIT a DIAGONAL UP-LEFT RAY in color C — paint cells at (h-1, c), (h-2, c-1), (h-3, c-2), ... until the ray exits the grid (hits row -1 or col -1). The marker stays at (h-1, c). Net: each bottom-row colored marker draws an upper-left diagonal line in its color.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
