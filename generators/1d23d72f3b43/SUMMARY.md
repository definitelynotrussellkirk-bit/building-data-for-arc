# 1d23d72f3b43 — fill each diagonal pair’s rectangle

Current version **3.1.0** samples zero-background grids with 2–4 foreground
colors, each appearing at exactly two opposite diagonal corners. The unchanged
rule fills each inclusive bounding box with that pair’s color. Different colors’
boxes do not overlap.

Ordinary draws include both diagonal orientations and vary solid, horizontal,
vertical and general rectangle profiles. Exact controls are `grid_h`, `grid_w`
and `n_pairs`; unknown controls reject. All five canonical inputs are accepted.
The retained main-diagonal-only rival and its counterexample explain the
curriculum repair. See `notes.md` for source-bound checks and finite coverage
limits. Approval is derived from current code and retained evidence.
