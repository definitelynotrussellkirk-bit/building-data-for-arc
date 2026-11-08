# d8a6f767016a

For each separated 4-connected color-8 object, count the enclosed 0-regions in
that object's own bounding box and recolor the whole object by
`1→1, 2→3, 3→2, 4→4`; every other count remains color 8.

Kind: `per_puzzle`. Version: `4.0.0`. `RULE_HASH=feb6e892870b`.

The production lesson uses four demonstrations and one query. Consecutive
sample indices cycle through `count_2`, `count_3`, `count_4`, and `else_0`, while
every ordinary draw also includes a 14-cell one-hole frame. That frame is an
explicit counterexample to the strongest canonical-training shortcut, which
classifies objects only by component-size bands.

Public exact overrides are limited to `grid_h=9..16` and `grid_w=11..18`.
Unknown keys are rejected. `self_check` enforces the documented palette,
background, object-count, object-size, hole-count, and full-zero-ring domain.

Approval and training admission remain catalog decisions; this review does not
change them.
