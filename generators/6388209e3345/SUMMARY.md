# 6388209e3345

Fixed 3×11 grid containing THREE 3×3 PANELS separated by SOLID color-8 (cyan) VERTICAL DIVIDERS at columns 3 and 7. Panel 0 (cols 0-2) and Panel 1 (cols 4-6) are PROTOTYPE panels each containing a small shape (3-4 cells) in distinct non-{0, 8} colors with DIFFERENT shapes (different cell-supports to avoid ambiguity). Panel 2 (cols 8-10) is the QUERY panel: it contains the support of EXACTLY ONE of the two prototypes under some dihedral TRANSFORM (id, r1, r2, r3, fh, fv, tr, atr — one of the 8 D4 symmetries), painted in its own query color. Rule: identify which prototype's SHAPE matches the query panel's shape MODULO any of the 8 rotations/reflections. Output is a 3×3 grid containing the MATCHED PROTOTYPE in its ORIGINAL color and original orientation (not the query's transform). Net: pick the matching proto, output it.

Kind: `per_puzzle`. Imported version: `3.1.0`.
Approval is derived by the catalog from current code and retained evidence.
