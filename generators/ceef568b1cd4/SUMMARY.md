# ceef568b1cd4 — keep odd-area objects

Version **3.1.0**. Canonical Racket rule hash **8abfb7183f00**, unchanged.
Keep each odd-area, same-color, four-connected component at its original
position and color. Erase even-area components to background zero.

Default draws alternate independently randomized canonical-scale scenes and
five-object scenes that distinguish seven executable alternative rules. The
rich scenes contain both an odd/even same-color pair and an odd/odd same-color
pair, with diagnostic diagonal and cross-color edge contacts. All object areas
1..9 and foreground colors 1..9 are supported.

Exact controls: `grid_h` and `grid_w` 7..20; `n` 2..6 components;
`n_distinct_colors` 1..6, no greater than `n`. Realized controls are extracted
from pixels. Former inert palette/texture/density controls now fail explicitly.

Use three demonstrations and one query from consecutive default draws. Each
four-pair window has two rich witnesses, so any single-pair query holdout retains
a witness. Explicit overrides do not carry that default lesson guarantee.
Finite tests concern the declared alternatives, not universal identifiability.

`self_check` validates the broader teaching domain; `strict_canonical_like`
separately recognizes the original-scale, distinct-color, area-1..4 family.
See `notes.md`, the portable tests, and `workspace/reference_probe.py`.
Approval remains a catalog/maintainer decision bound to the exact source.
