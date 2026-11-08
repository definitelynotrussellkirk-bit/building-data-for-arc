# 8fca6bf05488 — cast vertical rays downward

Every nonzero input cell is a source. Its color is painted from the source row
through the bottom edge in the same column. Sources are processed in row-major
order, so a lower source overwrites the lower suffix of an earlier source in the
same column.

Kind: `per_puzzle`. Generator version: `2.0.0`. Canonical rule hash:
`fe26cc0d2dfe`.

The four-example teaching schedule cycles through `canonical`, `stacked`,
`bottom_boundary`, and `repeated_color`. These profiles expose overwrite,
bottom-edge, and repeated-color behavior that the five canonical pairs alone do
not distinguish from several simple shortcuts.
