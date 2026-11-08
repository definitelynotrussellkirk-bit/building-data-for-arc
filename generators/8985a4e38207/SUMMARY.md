# 8985a4e38207

0-bg grid (h, w ∈ [4, 14]) with: (a) ROW-0 TEMPLATE — a set of TEMPLATE COLS (1..w/2 cells) painted DOT COLOR (any non-0 non-2 color) at row 0 using a chosen layout (scattered/left/right/even/endpoints/alternating); (b) MARKER ROWS — for 1..h/2 ROWS r > 0, a MARKER cell of the same DOT COLOR is placed at a MARKER COL (chosen as last/first/random from cols NOT in the template). Rule (EXPAND MARKER ROWS AT TEMPLATE COLS WITH COLOR 2): identify the TEMPLATE COLS (non-0 cells in row 0) and the DOT COLOR. For EACH ROW r > 0: if r has ≥1 non-0 cell at any col NOT in the template (a marker), then PAINT every TEMPLATE COL of row r with COLOR 2 (red). Marker cells stay at dot color. Row 0 (template) stays. Rows without markers stay all-0. Net: each marker-row gets red dots at the template columns, marking the intersection.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
