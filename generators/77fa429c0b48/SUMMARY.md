# 77fa429c0b48

0-bg grid (h~9-11, w~10-12) with: (a) ONE connected MOTIF (3-5 cells, polyomino-shaped) in some non-{0, 8} color, placed at a random position; (b) EXACTLY ONE color-8 (cyan) MARKER single-cell, placed elsewhere with no non-bg neighbors. Rule: find the motif (the largest connected non-{0, 8} component) and the marker (the lone color-8 cell). Compute the motif's bbox and CENTER. ERASE the motif from its current location and PASTE its bbox-cropped image onto the grid CENTERED at the marker cell. The marker is OVERWRITTEN by the motif (or remains if not covered). Net: input has a motif + a far-away marker; output has the motif relocated so its center sits where the marker was.

Kind: `per_puzzle`. Imported version: `2.0.1`.
Approval is derived by the catalog from current code and retained evidence.
