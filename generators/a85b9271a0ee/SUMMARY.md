# a85b9271a0ee

A 6..12 by 6..12 zero-background grid containing exactly 3..12 nonzero cells in 1..3 separated, monochrome components. Different components use distinct colors, and at least one component contains an orthogonal corner. The edge_mode axis is either in_bounds (every cell has a valid (+1,+1) destination) or mixed (at least one cell clips at the bottom/right edge while at least one cell moves). The output rule starts from a fresh zero canvas and shifts each nonzero cell by (+1,+1), dropping out-of-bounds destinations.

Kind: `per_puzzle`. Imported version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
