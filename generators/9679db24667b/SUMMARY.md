# 9679db24667b — Marker Takes the Row Color

For each row, collect the distinct colors outside `{0, 9}`. If there is exactly
one such color and the row contains one or more `9` cells, replace **every** `9`
in that row with the companion color. All other rows stay unchanged.

Version `3.0.0` keeps the canonical Racket rule unchanged and replaces the old
input sampler with an exact, observable three-axis generator:

- `grid_h`: 6..10
- `grid_w`: 8..12
- `n_positive_rows`: 1..3

The default two-slot curriculum alternates:

1. `canonical`: sparse qualifying rows with one `9`; every default slot uses
   one of the four exact public `(height, width, palette-size)` profiles;
2. `teaching`: the same positive rule plus multiple `9`s, repeated companion
   cells, one 9-only row, and one two-color-plus-9 row.

Every teaching input refutes the declared shortcuts “replace only the first 9,”
“require one companion cell rather than one distinct color,” “use the first or
majority color on multicolor rows,” and “borrow a color for 9-only rows.” Three
consecutive demonstrations and every 3-of-4 rotation therefore retain a
teaching example. Canonical authority pin: `RULE_HASH = 7ebc4d35864a`.
