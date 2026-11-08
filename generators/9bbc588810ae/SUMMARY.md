# 9bbc588810ae — Prototype lookup up to symmetry

A 5x23 input contains four 5x5 panels separated by full-height color-9 columns. The last panel is the query; the first three are colored source prototypes. Find the unique source whose cropped shape maps to the normalized query under one of the **seven distinct transformations actually implemented by the frozen Racket authority**, then paint the query's original cells with that source color.

The authority's nominal `rot270` branch duplicates transpose, so `r3` is deliberately not advertised as an exact axis. Generated queries are asymmetric 4–8-cell polyominoes. One source is the exact match, one is a non-dihedral decoy with the same cell count and bounding-box dimensions, and one has a different cell count. A four-sample curriculum cycle places the decisive lower-color decoy witness twice, making every three-demo lesson—and every one-query rotation of a four-pair lesson—refute the strongest canonical-fitting bbox/count/lowest-color shortcut.

Kind: `per_puzzle`. Selected implementation: `3.0.0`. Canonical `RULE_HASH`: `a63dd2ae1f7a`.
Approval remains derived by the catalog from current code and retained evidence.
