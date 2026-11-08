# 021ea70e8ed8

0-bg grid (h~6-9, w~4-6) with 1-3 selected COLUMNS, each containing exactly 2 cells of the SAME non-zero color placed at DIFFERENT rows (separated by ≥2 empty rows); columns may SHARE a color, and near-miss content (mixed-color columns, 3-cell columns, horizontal pairs) stays unconnected. Rule: for each non-empty column, find the two same-color endpoint cells and CONNECT them by drawing a VERTICAL LINE of that column's color through every cell between them (inclusive of endpoints). Net: input has pairs of dots in each non-empty column; output has those dots replaced by solid vertical color segments spanning between the endpoints.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
