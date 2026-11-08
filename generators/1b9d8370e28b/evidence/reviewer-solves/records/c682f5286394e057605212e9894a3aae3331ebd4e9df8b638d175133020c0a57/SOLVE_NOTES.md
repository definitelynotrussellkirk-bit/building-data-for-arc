# Solve notes

The visible examples have a single straight boundary between background colors
1 and 8. Red cells keep their row and their count, but their horizontal
positions change. In every row belonging to background 8, the red cells are
packed against the left edge of that region; in background 1 they are packed
against the right edge.

For a horizontal split, each row has one full-width region. For a vertical
split, the count must be computed separately on the left and right sides of the
boundary. Connected-object shape is not preserved: the third demonstration has
a ragged object whose rows pack independently.

Implementation plan: infer the unique horizontal or vertical 1/8 split while
treating red cells as masks, restore the clean two-color background, count red
cells per row and region, then paint a left- or right-aligned run according to
the region's background color.
