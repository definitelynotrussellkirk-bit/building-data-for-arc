# ea957ff0d072 — Sequential Arrow Slides

A black grid contains one full-height color-8 wall and two or three distinct colored polyominoes. Each object touches one marker whose **color**, not its placement, specifies motion: 1=left, 2=right, 3=up, 4=down. Remove all marker cells first. Then process the original marker positions in row-major order; at each marker, select the currently adjacent non-wall object and slide its whole same-color component repeatedly in the marker direction until the next translation would cross the grid or collide with the current nonzero state. Earlier moves can therefore change or block later moves.

The four-example schedule contains three canonical-scale anchors plus one mixed-attachment counterexample. Together they expose all four marker colors, slide-until-blocked behavior, the wall as an obstacle rather than a destination, and row-major sequential interaction. Horizontal and coordinated vertical reflections add lawful geometric diversity without losing those lesson guarantees.

Kind: `per_puzzle`. Generator version: `4.0.0`. Pinned canonical rule hash: `d849dec31c02`.
Approval remains derived by the catalog from current code and retained review evidence.
