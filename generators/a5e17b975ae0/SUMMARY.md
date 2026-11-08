# a5e17b975ae0 — Fill Keyed Chambers

A lawful input is a 12–14 × 17–20 zero-background grid with exactly two detached hollow color-9 rectangular frames. Color-5 walls partition frame interiors into multiple 4-connected chambers. One or two distinct key cells from `{1,2,3,4,6,7,8}` occupy separate open regions, and at least one region remains unkeyed.

The selected rule floods each key color through the key's original 4-connected region of `0`/same-color cells. Colors 5 and 9 are barriers and remain unchanged; unkeyed chambers remain 0. The canonical Racket authority is unchanged and pinned by `RULE_HASH = ced8e283e2c4`.

Generator version `3.0.0` exposes four pixel-recoverable exact controls:

- `grid_h`: `12..14`
- `grid_w`: `17..20`
- `seed_profile`: `single | separate | partitioned`
- `wall_profile`: `cross_gap | dual_cross | cross_tee`

A deterministic five-slot schedule covers all canonical `(height, width, palette-size)` profiles in every five consecutive draws; difficulty bands rotate the schedule rather than changing the task manifold. The generator declares executable semantic witnesses and competitors for the identity and “ignore color 5” shortcuts.

Final source SHA-256: `f6aa8282a799c77a75b3f696ac10a79e24ab406b6c1259fcad7defdd643188d4`.
