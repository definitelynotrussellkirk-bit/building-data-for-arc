# 26ac80084566 — Sweep shadow into a wall

A single colored shape casts horizontal shadows toward an interior, full-height
color-8 wall. Each occupied row starts at its own farthest shape cell. Shapes may
lie on either side; the rule does not fill a global bounding box.

Kind: `per_puzzle`. Current source version: `2.0.0`.

The sampler now covers both sides, movable walls, explicit gaps and placement,
eight templates, and strict overrides. Three consecutive default demonstrations
cover both directions, row-varying geometry, and foreground colors below and above
the wall color. The lesson checker evaluates actual demonstrations against seven
explicit rivals and never uses query answers.

Current review: 27 focused tests passed, with 41 distinct canonical Racket inputs;
three native lessons and all 12 query rotations passed the declared-rival check.
The canonical rule and frozen examples are unchanged. Approval remains separate.
See `notes.md` for support limits, commands, and retained evidence.
