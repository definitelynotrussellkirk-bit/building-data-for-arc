# 0f801939eff6

A 0-background grid contains exactly four separated monochrome 4-connected components. The generated curriculum crosses two independent distinctions: all colors unique versus one color reused on two disconnected components, and all component areas distinct versus one equal-area pair. Component areas are 1..7 cells; grids are 8..16 rows by 11..18 columns; colors are ARC colors 1..9.

Rule: extract each same-color 4-connected nonzero component separately, record `(area, color)`, sort by area descending and then color ascending, and emit one row in which each component color is repeated by its area. The generated row is always wider than the source grid, preserving the canonical 2-D-to-long-row reshape relation.

The deterministic four-profile schedule is `unique_distinct`, `repeated_distinct`, `unique_tie`, `repeated_tie`. Every three consecutive demonstrations include a disconnected-same-color witness against global color-frequency aggregation and an equal-area witness against position-based tie-breaking.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
