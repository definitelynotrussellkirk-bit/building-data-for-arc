# 5dbba35ed715

Fixed 5×13 grid with: (a) ROW 0 contains EXACTLY ONE non-zero MARKER cell at some random column; (b) ROWS 2-4 contain THREE 3×3 panels at cols [1-3] (panel A), [5-7] (panel B), [9-11] (panel C), each with a different shape (plus, frame, diagonal). Rule: read marker column. Map to a panel: col < 4 → panel A (output cols 1-3); col < 8 → panel B (cols 5-7); else panel C (cols 9-11). Output: the selected 3×3 panel from rows 2-4.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
