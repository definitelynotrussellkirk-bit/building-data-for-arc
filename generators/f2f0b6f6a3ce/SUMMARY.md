# f2f0b6f6a3ce

0-bg grid with 3-4 connected blobs in distinct non-zero colors at scattered positions, each a STRICTLY DISTINCT size (so 'largest' is unambiguous). Blobs are placed with a >=1-cell buffer so they stay separate components. Rule: collect non-zero 4-connected components (connectivity is color-blind), find the largest by cell count, and crop the input to its bbox. Output = that subgrid (the largest blob's cells in their color plus any interior zeros).

Kind: `per_puzzle`. Imported version: `2.2.0`.
Approval is derived by the catalog from current code and retained evidence.
