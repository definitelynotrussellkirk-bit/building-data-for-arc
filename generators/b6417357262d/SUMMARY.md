# b6417357262d

0-bg grid (h = 2*sh + 4, w = 2*sw + 4 with sh, sw ~3-4) with: (a) ONE isolated KEY CELL in {4 (OR), 6 (AND), 8 (XOR)} placed alone with 8-neighbor buffer; (b) ONE color-2 (red) shape A at (1, 1) with sh × sw bbox; (c) ONE color-3 (green) shape B at (sh+3, sw+3) with matching sh × sw bbox. A and B are connected within the sh × sw bbox but have DIFFERENT cell patterns. Rule: detect op key, A, B. Compute per-cell boolean combine of A and B (both normalized to bbox), with op = OR (key==4), AND (key==6), or XOR (key==8). Output: the combined pattern painted in color 7 (orange) at A's position. Other cells = 0.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
