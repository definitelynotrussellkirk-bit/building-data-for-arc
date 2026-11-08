# Blind solve notes — 8bc2bc6a9bb8

I used only `solve-blind/challenge.json` and my own Python reasoning.

## Observations

- The first row contains a left-to-right sequence of nonzero colors; all puzzle objects below it are gray (`8`).
- Each training input has the same number of header colors and 4-connected gray objects.
- Sorting gray objects by area from largest to smallest pairs them exactly with the header colors from left to right.
- The output preserves each object's orientation and bounding-box shape, recolors it with the paired header color, places objects left to right with one zero column between them, and bottom-aligns all bounding boxes.

Checks against the examples:

- Train 1 areas `5,4,2,1` pair with `9,4,5,7`; the 5-cell stair, horizontal four, vertical two, and singleton match the output.
- Train 2 areas `4,3,1` pair with `3,5,1`.
- Train 3 areas `3,1` pair with `2,9`.
- Train 4 areas `4,3,1` pair with `2,3,4`.

## Implementation

Find 4-connected components of `8` below the header, sort by cell count descending, crop each to its bounding box, recolor in header order, and pack with one-column gaps at a common bottom edge.

No failed natural revision preceded this implementation; the rule was consistent across all four visible examples.
