# be7f70e60fb7 — complete straight segments

On a sparse zero-background grid, group nonzero cells by color. For each color that appears **exactly twice**, fill the bounded horizontal or vertical segment between the two cells when they share a row or column. Preserve diagonal pairs, singletons, aligned triples, and every other cell.

Generator version `3.0.0` exposes one observable axis, `scene_profile`, and cycles a four-example semantic curriculum:

1. `canonical_two_pairs` — one horizontal and one vertical positive pair.
2. `canonical_three_pairs` — three positive pairs with both orientations represented.
3. `alignment_decoy` — two positive pairs plus a repeated diagonal color that must stay unchanged.
4. `cardinality_decoys` — one positive pair plus a singleton and a gapped aligned triple that must stay unchanged.

Every generated input uses one of the five exact canonical `(height, width, palette-size)` signatures. Connectable segments are noncrossing so the examples teach the intended rule rather than incidental overwrite order. The Python mirror is pinned to Racket authority hash `d264380c5850`.

Kind: `per_puzzle`. Imported version: `2.0.1`; reviewed version: `3.0.0`.
Approval is derived by the catalog from current code and retained evidence.
