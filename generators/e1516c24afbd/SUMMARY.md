# e1516c24afbd

Two equal-size panels are stacked vertically. The output has the size of one
panel and writes color 2 at `(r, c)` exactly when both aligned input cells are
0; every other aligned occupancy state maps to 0.

Kind: `per_puzzle`. Current version: `2.0.0`. Rule pin: `de03400353f9`.

Normal examples use distinct nonzero, non-2 colors for the two panels and
contain all four aligned occupancy states (`00`, `10`, `01`, `11`). Exact
controls cover dimensions 3..10, colors, 1..6 both-zero cells, and six
observable layouts. Declared semantic rivals and witnesses make lesson-level
identifiability executable rather than descriptive.

Approval is derived by the catalog from current code and retained evidence; this
summary does not admit the generator to training.
