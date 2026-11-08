# 55993f4c12af

Version `3.0.0`; canonical rule hash `ce2dee847896`.

The input is an even-height grid split into aligned top and bottom halves. Each
half has one distinct nonzero, non-yellow foreground color. The output has the
half-height and the same width: a cell is yellow (`4`) when either aligned input
cell is nonzero, otherwise black (`0`).

Every ordinary generated input contains all four aligned Boolean occupancy
states: both empty (`00`), top only (`10`), bottom only (`01`), and overlap
(`11`). This directly refutes top-copy, bottom-copy, XOR, AND, and constant-fill
rules inside each example. Exact public controls are `half_h`, `grid_w`,
`top_color`, `bot_color`, and `relation_profile`; all are validated and
recoverable with `observe_overrides`.

A four-slot deterministic curriculum gives one exact canonical 12x4 / colors
3,5 anchor per cycle and three off-canonical examples. Relation layouts are
randomized within exact balanced/top-heavy/bottom-heavy/overlap-heavy profiles;
`empty_heavy` is also available as an exact override. See
`workspace/lesson_probe.py` for a source-bound all-cyclic-start rival probe.
