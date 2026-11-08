# 733c1bac8c45 — pack each row’s population to the left

Version 3.0.0. Canonical rule hash: `816c15c8ae9f`.

On a zero-background grid, process rows independently. Count a row’s nonzero cells and write that many copies of its first nonzero color starting at column 0; fill the rest of the row with zero. Empty rows remain empty and grid dimensions are preserved.

The lawful teaching grammar uses 4–12 rows, 5–14 columns, and 3–9 active rows. Each active row has 1–5 copies of one color, active-row colors are distinct, row populations vary, at least two rows visibly move, and a gapped row forces multi-column compaction. Public exact axes are only `grid_h`, `grid_w`, and `active_rows`; retired palette/texture aliases now fail loudly.

The four-profile schedule supplies two canonical-scale cases (5×8 with three active rows and 5×9 with four) plus two taller cases with more than four active rows. The latter refute two shortcuts that fit all four stored canonical pairs: processing only five rows and processing only the first four active rows. Executable rivals, witnesses, a Python diagnostic mirror, and query-rotation checks support finite semantic verification; the Racket rule remains label authority.
