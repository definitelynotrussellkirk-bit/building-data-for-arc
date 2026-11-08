# f869ac2ae3e4

0-bg grid (size varies) with ONE single-cell MARKER and ONE connected multi-cell SHAPE (distinct non-0 colors). The marker sits beyond the shape's bounding box along one axis, with a gap. Rule: locate the size-1 marker and the larger shape; SLIDE the shape toward the marker along the axis where the marker is outside the shape's bbox, until the shape's leading edge is one cell short of the marker. OUTPUT a blank grid with the marker at its original position and the shape at its slid position. Net: the shape moves to dock against the marker. (Was mis-modelled as panels.)

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
