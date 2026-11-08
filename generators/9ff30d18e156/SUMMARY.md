# 9ff30d18e156 — Endpoint Segment Fill

Fill each repeated nonzero color's row-local minimum-to-maximum interval.
Version 2.0.0 samples clean endpoints, multi-hit colors, disjoint same-row color
spans, and their combination. Non-endpoint profiles can include singleton
distractors. Every draw has a productive span; collision-priority cases are
outside this generator's documented domain. Labels remain Racket-derived.

Actual controls: grid_h (3..10), grid_w (8..14), n_pairs (1..5 exact productive
rows, <=grid_h), and texture (endpoints|mixed|multihit|multicolor). Defaults
anchor canonical dimensions; overrides retain their full range in every band.
Old inert palette/density/position knobs and degenerate textures now error.

Kind: `per_puzzle`. Version: `2.0.0`. Racket pin: `efbc8aee85e7` (unchanged).
Approval remains derived from catalog evidence, not self-declared by this repair.
