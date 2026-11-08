# 70a3d3e2c975 — reflect source colors across the central 9-axis

Selected version: **3.0.0**. Canonical Racket authority remains unchanged and is pinned as `740ca06f408e`.

An integer grid has height 5..14 and odd width `2*half_w+1`, with `half_w` 2..8. A full-height central column is 9, the right half is initially zero, and source colors 1..8 occupy the left half. The reference copies every source cell to its reflection, preserving the source and axis.

Default samples alternate between two connected monochrome objects and scattered marks, with a seed-dependent phase. Object scenes retain canonical geometry, two source colors, and 6..7 source cells; scatter scenes span the broader geometry/count/palette ranges and include singleton, source-edge, and noncanonical-palette witnesses. Difficulty changes count weights while retaining valid exact controls. Generated shapes are constructed, not copied from canonical grids.

Exact controls: `grid_h`, `half_w`, `marks` (1..20), and foreground `palette_size` (1..8). `n_distinct_colors` remains a validated compatibility alias of `palette_size`, rather than a second independent axis. `texture` aliases `palette_kind` for default/warm/cool/varied palettes. `position_bias=left_half` and `density=mixed` are validated compatibility selectors. Impossible fully specified combinations and malformed/unknown controls fail explicitly; free geometry accommodates a feasible exact mark count. Diagnostic `full_left` requires exact area equality when marks are supplied. Empty-left and missing-axis fixtures are intentionally invalid and cannot bypass validation through metadata.

See `notes.md` and `workspace/HANDOFF.md` for limits, tests, and the replayable coverage probe. Approval remains a catalog/maintainer action tied to exact reviewed source bytes.
