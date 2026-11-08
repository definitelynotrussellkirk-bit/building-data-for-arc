# 983d0ea3bd17 — Beacon Cross Rays

Each red (`2`) source emits orange (`7`) rays up, down, left, and right. A ray paints only background-zero cells and stops at the grid edge or at the first nonzero input cell. Sources and blockers remain unchanged.

Version `4.0.0` pins canonical rule hash `fd605125c9f8` and exposes four honest override axes:

- `grid_h`: `6..10`
- `grid_w`: `8..12`
- `seed_count`: `2..3`
- `scene_kind`: `scattered | edge_anchored | row_aligned | col_aligned | blocked`

The default three-slot curriculum is:

1. `canonical_pair`: scattered, canonical-like, two sources;
2. `two_color_blocker_probe`: two independently observable blockers with different nonzero colors, an edge source, and an aligned source pair;
3. `canonical_triple`: scattered, canonical-like, three sources.

The blocker slot prevents four canonical-fitting shortcuts:

- painting through every nonzero cell;
- stopping only at blocker color `8`;
- treating every nonzero cell as an emitter;
- deduplicating sources that share a row or column.

Every three consecutive default examples contains one probe and both canonical anchors. The module includes a Python rule mirror, strict canonical predicate, observable override decoder, 12 named rivals, 10 rival-backed witnesses, lesson-identifiability checks, malformed-scene fixtures, 26 focused tests, and `workspace/deep_audit.py` for sliding-window adversarial audits.
