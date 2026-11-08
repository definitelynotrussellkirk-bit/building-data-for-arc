# 0d0f5035a157

Compact each row independently: remove zero cells, preserve the remaining values' left-to-right order, write them from column 0, and fill the suffix with zeros.

The v3.0.0 sampler produces 5–10 by 8–14 zero-background grids with one to nine nonzero colors. It exposes six exact pixel-observable axes (`grid_h`, `grid_w`, `palette_size`, `max_cells_per_row`, `n_empty_rows`, and `n_packed_rows`), mixes already-packed and genuinely moved rows, and alternates sparse canonical-linked cases with dense moved rows containing at least five values. Those dense rows refute the strongest canonical-fitting shortcut, “compact only rows with at most four nonzero cells.”

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
