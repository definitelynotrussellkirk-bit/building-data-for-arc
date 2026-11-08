# 78f3cf31c4bf — Missing 2x2 Corner

Version `3.0.0` is source-bound to canonical `RULE_HASH = "4954a1b1ccb4"`.

The rule is one simultaneous pass over the original input: for every 2×2 window
with exactly three equal nonzero cells and one zero, fill that zero with the
common color. The Python mirror is pure and the selected Racket authority was
not changed.

The six-slot curriculum retains three exact canonical size/palette profiles and
adds connected multi-window components, repeated target colors, mixed-color
near-matches, and closure traps. Every three consecutive default examples refute
five shortcuts that fit all four canonical pairs: component-bbox completion,
one completion per color, requiring exactly three cells of a color, ignoring
color agreement, and repeating the rule until stable.

Exact axes are `grid_h` (`6..14`), `grid_w` (`8..16`), `target_count` (`3..6`),
`color_count` (`1..3`), `layout_mode` (`isolated|connected`), and
`corner_diversity` (`2..4`). Two impossible joint tuples are declared explicitly;
every single-axis override remains realizable. No degenerate textures are exposed
through the production domain.
