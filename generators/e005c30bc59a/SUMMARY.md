# e005c30bc59a — reflected laser trail

A single non-corner border source in color 3, 4, 6, 7, 8, or 9 launches a beam inward. Color 1 is a slash mirror, color 2 is a backslash mirror, and color 5 is a wall. The beam paints each traversed black cell with the source color, turns at reached mirrors, and stops at a wall or the grid boundary. Mirrors, walls, and the source remain unchanged. A cell may be traversed again from a different direction; only a repeated `(row, column, direction)` state is a loop.

The v4 generator is route-aware. Every ordinary draw has a non-trivial trail that reaches at least one mirror. Four cyclic lesson roles jointly cover all source edges, non-7 source colors, both mirror orientations, wall stops, boundary exits, optional off-route distractors, and one perpendicular path crossing that visibly continues after the revisit. Exact semantic override axes are observed by `observe_overrides`; declared rivals and witnesses make lesson identifiability executable.

Kind: `per_puzzle`. Current version: `4.0.0`. Canonical Racket authority is unchanged and pinned by `RULE_HASH = 9114178dd0f7`.
