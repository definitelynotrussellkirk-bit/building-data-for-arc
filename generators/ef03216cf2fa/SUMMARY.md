# ef03216cf2fa

Three or four separated monochrome objects have controlled canonical-size profiles, distinct bounding-box perimeters, mixed orientations, and observable row-major rank layouts. Crop each object, rotate tall crops 90 degrees clockwise, sort by perimeter descending (row-major on ties), and stack the crops vertically, left-aligned, with one zero row between them.

Every generated input contains at least one asymmetric tall crop, so clockwise and counterclockwise rotation produce different outputs. The generator exposes six exact controls (`grid_h`, `grid_w`, `n`, `tall_count`, `rank_layout`, and `palette_family`), validates all overrides, accepts the canonical examples (including tied canonical perimeters), and provides executable semantic rival/witness hooks.

Kind: `per_puzzle`. Reviewed version: `3.0.0`. Canonical Racket authority unchanged; pinned rule hash: `455db4f731f0`.
Approval is derived by the catalog from current code and retained evidence.
