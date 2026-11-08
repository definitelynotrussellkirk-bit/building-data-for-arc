# Native parametric family: L-completion fill mode

`fill_mode=object_color` is the exact selected canonical Racket program: find
each same-color three-cell L in a 2x2 box and fill its missing corner with the
object's color.

`fill_mode=orientation_legend` adds a four-color top-row legend in NW, NE, SW,
SE order. Step A discovers each L's missing corner and derives its orientation
index. Step B consumes that index to choose the corresponding legend color and
paint the missing cell. Every scene contains all four orientations and at least
one orthogonal contact between differently colored Ls, so both the setting and
the colored-object semantics are visible. The fourth query is a substantive
30x30 case.

The sampler is deterministic, uses identical inputs across settings, supports
2-6 demonstrations and exactly four private queries, and keeps the canonical
default byte-for-byte.
