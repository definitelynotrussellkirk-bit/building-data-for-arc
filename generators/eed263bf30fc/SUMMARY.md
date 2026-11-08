# eed263bf30fc

2N+1 by 2N+1 grid with one full color-9 row (separator row) and one full color-9 column (separator col), splitting the grid into 4 N×N panels. Top-left has a small shape A in some color cA. Top-right is t(A) for some transform t in {rot-cw, rot-180, rot-ccw, flip-lr, flip-ud}. Bottom-left has a different shape Q in color cQ (cQ ≠ cA possibly). Bottom-right is empty. Rule: find separators, split into panels, detect transform t. Apply t to Q. Paste t(Q) into bottom-right. Output = input + filled bottom-right.

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
