# bb432515d2e6

A 10–12 × 11–14 zero-background grid contains a complete rectangular color-5 wall frame and two or three distinct singleton seed colors. Color 5 is impassable. For every zero cell, compute four-neighbor shortest-path distance to each seed through non-wall cells; paint the unique finite nearest seed color, but preserve finite ties and cells in seedless components as zero. Walls and seeds are unchanged.

Version `3.0.0` uses three recoverable lesson profiles in a deterministic three-example cycle: `open_tie`, `wall_detour`, and `seedless_chamber`. Together they distinguish the selected rule from deterministic tie-breaking, component-local Manhattan distance, and filling unreachable chambers. Public exact controls are `grid_h=10..12`, `grid_w=11..14`, `n_seeds=2..3`, and `profile`.

Kind: `per_puzzle`. Canonical rule hash: `823ef34eb751`.
