# Parametric rule assessment — d185ceed5cc1

Two small rule parameters were considered, as required by the review duty. Neither is suitable for the selected training path, so no executable variant is promoted.

## 1. Gravity direction: `{left, right}`

A mechanically valid prototype could replace right-packing with left-packing and choose the direction once per episode. Demonstrations containing movable pebbles would distinguish the two rules. However, the current packet binds every generated label to one pinned canonical Racket authority (`a1ebff603893`), and the input contains no direction cue. Mixing left- and right-gravity episodes under one task ID would therefore create hidden episode-level label semantics and invalidate the source/rule binding. A separate task/rule identity would be required.

## 2. Wall color: `{1..9}`

The implementation could parameterize the separator color, but the canonical role is specifically color `8`, while the remaining nonzero colors are ordered pebbles. Because lawful inputs use the full palette, changing the wall color without an explicit role marker would make the role ambiguous and would again require a separately pinned rule. Treating wall color as a free generator axis while retaining the existing authority would be incorrect.

## Decision

Keep both parameters fixed in the selected generator: gravity is rightward and walls are color `8`. This preserves exact authority binding and avoids hidden per-episode rules. A future experiment may create separately identified left-gravity or alternate-wall tasks, but those variants should not share this task’s canonical execution path.
