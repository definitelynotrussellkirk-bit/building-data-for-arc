# 9e80ef661ecc

Preserve each same-color orthogonally connected object in place and recolor it
only by its topological hole count: **0 → 2, 1 → 3, 2 → 4, 3 → 6, 4+ → 9**.
A hole is a complement region enclosed by the object's own cells inside its
bounding box; touching cells of different colors remain different objects.

The four-example curriculum cycles through:

1. `canonical` — alternates small public-like grids with varied connected masks;
2. `equal_features` — same-colored 4×4, area-14 masks with 0/1/2 holes,
   including diagonally adjacent cavities;
3. `touching` — same-colored diagonal contact and different-colored orthogonal contact;
4. `extended` — every hole count 0 through 6, explicitly teaching 4+ → 9.

Ordinary and extended masks vary cavities, boundary notches, quarter turns,
dimensions and object count. Diagnostic profiles share overlapping canvas sizes;
duplicate hole counts and contact with every canvas border have sampled support.
Profile recognition uses structure rather than canvas dimensions.

The measured 300-lesson census refutes all **12 declared rivals** in every
four-demo lesson, including row-gap counting, 8-connected holes/objects,
four-only mapping and the frozen v3.0 shape lookup. All 1,500 outputs match the
unchanged Racket authority. This is finite evidence against named rivals.
Normalized scene signatures are object multisets; they omit spatial relations.

Kind: `per_puzzle`. Version: `3.1.0`. Canonical rule hash: `609d24e8c088`.
