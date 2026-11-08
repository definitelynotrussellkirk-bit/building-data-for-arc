# 5aeb34b3b850

0-bg grid (h~8-12, w~10-14) with SEVERAL CONNECTED COMPONENTS of COLORS 2, 3, 4 — n2 (1-3) red, n3 (1-3) green, n4 (1-3) yellow blobs, each of size 1-2 cells, at scattered non-touching positions. Counts are typically distinct to avoid symmetric output. Rule: COUNT the CONNECTED COMPONENTS of EACH color: n2 = count of color-2 components, n3 = color-3, n4 = color-4. Build a SINGLE-ROW OUTPUT: n2 cells of COLOR 2, then 1 cell of COLOR 0 (separator), then n3 cells of COLOR 3, then 0 separator, then n4 cells of COLOR 4. Output dimensions: 1 × (n2 + n3 + n4 + 2). Net: input has scattered red/green/yellow blobs; output is a horizontal count-row encoding.

Kind: `per_puzzle`. Imported version: `3.1.1`.
Approval is derived by the catalog from current code and retained evidence.
