# 39574cf4b561

A zero-background grid contains three or four active colors. Each active color appears at exactly three corners of an axis-aligned rectangle; the output adds the same color at the empty fourth corner. Exactly one other nonzero color is an irrelevant singleton and is preserved.

The curriculum keeps the four canonical-linked `(height, width, active-color-count)` profiles: `10x10/3`, `11x11/3`, `11x11/4`, and `12x12/3`. It varies missing-corner patterns, active-color palette bands, rectangle placement, and whether the singleton lies inside or outside a rectangle bounding box.

Canonical inputs always use color 9 as the singleton, which admits the plausible shortcut “never complete color 9.” Version 3.1.0 therefore schedules two canonical-role examples followed by one shortcut-breaking example in which color 9 is an active rectangle and another color is the singleton. Every sliding three-example lesson contains both roles while retaining a `2/3` strict-canonical share.

Kind: `per_puzzle`. Selected version: `3.1.0`. Rule hash: `6af9170b5713`. The selected Racket authority is unchanged.
