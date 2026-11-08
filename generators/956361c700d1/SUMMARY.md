# 956361c700d1

Small grid (3..6 rows × 11 cols) split into THREE 3-col panels by full-height color-5 (gray) divider columns at cols 3 and 7. Panel A (cols 0-2) and Panel B (cols 4-6) share the SAME color (call it color X) — B's binary shape is some dihedral transform t of A's shape. Panel C (cols 8-10) uses a DIFFERENT color (color Y). C's shape is independent. Rule: split panels at 5-columns. Infer the dihedral transform t such that t(A.shape) == B.shape (search id, rot90, rot180, rot270, flip-lr, flip-ud, diag, anti-diag). Apply t to C (preserving C's color). Output = t(C), 3×3.

Kind: `per_puzzle`. Imported version: `2.1.1`.
Approval is derived by the catalog from current code and retained evidence.
