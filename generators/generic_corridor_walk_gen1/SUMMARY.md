# generic_corridor_walk_gen1

gen1: staircase corridors walked with repeating patterns.

Scene: a bg terrain holds 1-2 one-wide staircase CORRIDORS of a second
terrain (segments >= 3, non-consecutive cells kept >= 2 apart) plus a few
detached corridor-colored blobs; a legend row of 2x2 swatches (pattern),
a 2x2 turn-marker square, and a pattern[0]-colored single cell at each
corridor's border mouth. Transform: walk each corridor painting the
pattern, stamp the marker color ahead at each turn, dissolve the legend
squares. Scenes resample until the walk covers the constructed corridor
exactly.

Kind: `generic`. Imported version: `1.0.0`.
Approval is derived by the catalog from current code and retained evidence.
