# 34df88dbd435

0-bg grid with several connected objects of varied aspect ratios. At least one TALL (bbox h > w), one WIDE (bbox w > h), and one SQUARE (bbox h == w). Objects in any non-{0, 2, 4, 8} color (avoid output colors). Objects separated by ≥1-cell buffer. Rule: for each object, compute bbox h and w. If h > w → recolor to 2 (tall). If w > h → recolor to 8 (wide). If h == w → recolor to 4 (square). Output preserves grid shape.

Kind: `per_puzzle`. Imported version: `2.0.0`.
Approval is derived by the catalog from current code and retained evidence.
