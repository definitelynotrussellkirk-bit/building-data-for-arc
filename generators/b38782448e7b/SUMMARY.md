# b38782448e7b

Canonical-scale grids use a unique modal background. Non-background row-0 cells
are controls: a control fires only when it differs from the cell directly below
it. In every firing column, rows 1 onward are replaced by an XOR-like vertical
sweep: marker-color cells become background and every other color becomes the
marker. Equal row-0/row-1 controls are inert decoys, and all non-firing columns
are preserved.

Generator version `3.0.0` advertises six strict observable axes: `grid_h` 20–30,
`grid_w` 20–30, `bg_color` 0–9, `palette_size` 3–7, `n_markers` 2–6, and
`n_decoys` 0–3. Default profiles cover the canonical 20×20/palette-3 and
30×30/palette-6/7 regimes, include a variable-position canonical-scale component
with an attached color mosaic, keep connected-object counts inside the canonical
envelope, and teach four executable rivals through explicit witnesses.

Kind: `per_puzzle`. Canonical rule hash: `06479b7ecc39`.
Approval is derived by the catalog from current code and retained evidence.

Owner acceptance: current generator 3.0.0; imported baseline 2.0.1 is historical. Archival raw_code in both selected solution records is preserved; only executable target_code is synchronized to the canonical authority. The two audit targets remain unresolved.
