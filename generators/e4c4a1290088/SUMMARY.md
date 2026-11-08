# e4c4a1290088

Equality matrix from row and column headers.

Version: `3.0.0`. Canonical rule pin: `b1a9cb7a0f30`.

The input preserves a color-0 interior plus a header row and header column. An
interior cell receives its column-header color exactly when that color equals
the row header. The default curriculum interleaves all three official
shape/palette profiles with broader 6–18 cell grids, and every instance exposes
an off-diagonal equality, multiple labels, and a nonzero mismatch.

Exact axes: `grid_h`, `grid_w`, and `n_labels`. All declared values are legal in
every difficulty band and recoverable through `observe_overrides`.
