# 5419b6df2873

0-bg grid (h×w, ~5-9 by ~6-10) where the TOP ROW contains 2-5 non-zero marker cells in distinct colors at distinct columns. Optionally a few scattered non-zero cells in lower rows (to test that the rule erases, not preserves, non-top-row content). Rule: build a fresh output grid of identical dimensions. For each column c, if top-row marker g[0][c] is non-zero with color v, fill the entire column c with v. Empty marker columns stay all-zero. Lower-row content from input is discarded.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
