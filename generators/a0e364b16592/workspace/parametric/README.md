# Native blocker gravity with an input-derived cue side

`canonical_down` is the exact selected canonical Racket program: color 5 stays
fixed and every other nonzero cell falls to the bottom of its own color-5-bounded
column segment while preserving top-to-bottom order.

`cue_side` adds one fixed singleton color-9 cue on the top or bottom border.
Step A locates that cue and derives the intermediate direction (`up` for a top
cue, `down` for a bottom cue). Step B treats colors 5 and 9 as fixed boundaries
and packs every payload segment toward the derived side. Forcing the opposite
intermediate changes the final output on the retained causal case.

The setting is fixed per episode. Inputs are matched across settings and built
before slicing, with 2–6 prefix-stable demonstrations and 1–4 prefix-stable
queries. The first two demonstrations use opposite cue sides and blocker-rich
multi-color segments. The complete bank includes varied rectangular geometries,
multiple blockers in tall scenes, boundary contacts, and substantive 30x30 demo
and query scenes. Public helpers expose one answer-masked query and hash only
those visible bytes.

The production generator was also repaired: each ordinary draw now contains a
real color-5 blocker with payload above and below it, closing the historical
`global_bottom_gravity_preserve_5` shortcut without changing the canonical rule.
