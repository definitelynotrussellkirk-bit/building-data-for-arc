# 8384d9743be8

Fixed 5×11 grid, 0-bg, with TWO 5×5 PANELS separated by a blank column at col 5: LEFT PANEL at cols 0..4 has one CONNECTED binary shape in color 1, RIGHT PANEL at cols 6..10 has one CONNECTED binary shape in color 1. The two panels share AT LEAST ONE overlapping cell position (so intersection is non-empty) and AT LEAST ONE different cell (so XOR is non-empty). Rule: read the binary masks A (left) and B (right, shifted to local coords). Compute 3 boolean masks: UNION, INTERSECTION, XOR. Output: an HSTACK of 3 5×5 BOOLEAN PANELS with 1-col separators — UNION (color 2), INTERSECTION (color 3), XOR (color 4). Net: 2-panel boolean algebra → 3-panel gallery showing union, ∩, XOR.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
