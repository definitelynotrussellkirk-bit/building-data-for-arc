# efb59efe0080

Version `3.0.0`; canonical rule hash `1cb444e6f050`.

A canonical-profile 0-background canvas contains one connected red (2) mask and one connected green (3) mask. Crop each mask to its own bounding box and align the two top-left corners. Output cyan (8) at cells occupied by exactly one normalized mask, then crop the XOR result to its nonzero bounding box.

The reviewed generator exposes three exact controls: `canvas_profile`, `size_2`, and `size_3`. Connected 4–8-cell masks are drawn constructively from exhaustive 3×3 catalogs. Every pair overlaps, has exclusive cells on both sides, refutes filled-bbox and absolute-position shortcuts, and alternates between final-crop-required and crop-noop schedule profiles.

Selected Racket authority is unchanged. Final generator SHA-256: `0317cd7ebf2fd286ff60e54b72c1c7e002cb75cc581f6dd8523250c1ed5eaf53`.

Verification: 12/12 final battery stages green, 21/21 task tests, 300/300 source-bound lessons free of declared-rival ambiguity, and 0/4,800 cyclic query rotations ambiguous for the five named rivals. These finite checks do not prove universal identifiability.
