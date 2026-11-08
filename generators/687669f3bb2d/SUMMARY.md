# 687669f3bb2d

0-bg grid (h~11-13, w~13-15) with multiple ISOLATED color-3 (green) connected components. EXACTLY ONE is VERTICALLY (LR-mirror) SYMMETRIC — its normalized cells are invariant under flip-lr. The other 1-2 components are ASYMMETRIC under that mirror. Components are buffered by ≥1 bg cell on all sides. Rule: scan color-3 objects in scan order. Pick the FIRST one whose normalized cells are LR-mirror symmetric. Compute its scaled offsets at factor 2 (each cell becomes a 2×2 block). Output is a small grid sized to fit the scaled cells, painted color 8 (cyan).

Kind: `per_puzzle`. Imported version: `3.2.0`.
Approval is derived by the catalog from current code and retained evidence.
