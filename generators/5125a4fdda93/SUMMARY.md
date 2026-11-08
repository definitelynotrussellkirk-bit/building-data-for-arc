# 5125a4fdda93

0-bg grid (h~9-13, w~12-17) with: (a) ONE color-3 (green) TEMPLATE shape — a small polyomino [(0,0),(0,1),(1,1),(2,1)] placed at upper-left (rows 0-2, cols 1-2); (b) THREE CONTROL MARKERS placed at fixed positions ((h-5, 4), (h-4, w-5), (h-2, 2)) in 3 distinct colors drawn from {1, 2, 4, 6} — each marker color encodes a DIFFERENT ROTATION (0°, 90°, 180°, 270° respectively). Rule: extract the green template. For each control marker, decode the rotation from its color and STAMP a rotated copy of the template in color 3 at the marker's position. Original template and markers are DISCARDED. Output: 3 green copies of the template, each rotated according to its marker, at the marker positions. Net: marker colors program rotations; output is the template gallery.

Kind: `per_puzzle`. Imported version: `2.0.2`.
Approval is derived by the catalog from current code and retained evidence.
