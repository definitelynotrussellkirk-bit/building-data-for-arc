# Working notes: b3bfd59c2c43

## Review 2026-10-03 — assignment review-dc30427a56c13c3f

### Baseline findings

The pinned `1.3.1` source advertised nine axes but did not honor or observe most
of them. Its before battery finished with 7 passing, 2 advisory, and 3 failing
stages. The blocking failures were:

- missing `RULE_HASH` and dead/singleton axis declarations (`lint`);
- overlapping ordinary/degenerate texture domains plus a one-condition
  `self_check` that accepted empty or structurally unrelated inputs
  (`defect_lint`); and
- thousands of exact-override findings, including silently accepted unknown
  keys, dimensions ignored by degenerate branches, and drawn axes absent from
  returned pixels (`override`).

The profile gate measured `0/60` exact canonical-profile draws. The semantic
gate reported `NO_CONTRACT`. The old thin plus/H/T/diamond shapes also frequently
had no depth-two cell, so demonstrations could teach “recolor the entire object”
instead of boundary peeling.

Evidence: `checks/before/` and `checks/before-driver.log`. An earlier interrupted
run is preserved separately at `checks/before-interrupted/`.

### Selected repair

The source was replaced with a constructive task-specific sampler rather than
patching the false metadata around the old stochastic rectangle routine.

- Pinned the selected authority as `RULE_HASH = "28b8cf49f820"` and bumped the
  generator to `2.0.0`; the Racket rule itself was not changed.
- Reduced the public control surface to one exact categorical axis,
  `canvas_profile`, whose three values are all canonical profiles and are
  recoverable from the returned grid.
- Constructively places exactly two thick components with a one-cell Chebyshev
  moat. Every component contains a true interior cell.
- Uses exactly two input colors from `1..7`; `8` remains output-only and `9`
  remains excluded from generated inputs.
- Schedules `canonical`, `edge`, and `multicolor` profiles on
  `sample_index % 3`. Any three consecutive demonstrations therefore exercise
  all scheduled branches regardless of lesson start.
- Added an independent Python rule mirror, four executable rivals, four
  witness-to-rival claims, two canonical-compatible shortcuts, and a
  `lesson_identifiable` check.
- Added strict structural validation, exact override observation, and loud
  rejection of unknown axes or invalid difficulty values.

### Rejected alternatives

- **Keep all old axes and repair each branch:** rejected because dimensions,
  counts, palette aliases, texture modes, and difficulty-specific ranges were
  mutually inconsistent. Preserving them would retain a large Cartesian
  override surface with no training value.
- **Use only monochrome rectangles:** rejected because every canonical pair is
  also explained by a per-color boundary rule. A multicolor connected component
  is required to distinguish occupancy components from color components.
- **Keep components away from every canvas edge:** rejected because the selected
  rule explicitly treats off-grid cardinal neighbors as exposure, while the
  canonical edge-touching example does not independently falsify an edge-blind
  implementation.
- **Allow thin lawful degenerates in ordinary lessons:** rejected because they
  erase the observable difference between boundary peeling and recoloring the
  whole component. The selected training manifold requires a nonempty interior
  in both components.
- **Advertise separate `grid_h` and `grid_w` axes:** rejected because the task
  has three correlated canonical profiles, not a full height-by-width product.
  One categorical profile axis states and tests the real contract.

### Final measured evidence

Source SHA-256 used by the focused and stage checks:
`8518cf4214cd387ef4974e3bd8efef3ae2a8989ac19e065b6b6d567cf181a793`.

- Focused task tests: 22 passed.
- Override contract: 360/360 accepted, 4 cases, 3 bands, zero findings.
- Canonical profile floor: 60/60 exact profile; all 3 canonical inputs accepted.
- Semantic gate: 600/600 strict; 4/4 witnesses firing; 4/4 rival claims verified;
  12/12 smoke lessons identifiable.
- Source-bound extended probe: 300 lessons (100 per band), 1,200/1,200 unique
  inputs, zero invalid grids, zero Python-oracle mismatches, zero ambiguous
  lessons, and zero survivors for all four competitors. Corpus SHA-256:
  `da655f8c19ec8986325e0dafc99beee6932c928d0a5c2f6c8ecc46e686eb0be9`.

Extended evidence: `checks/lesson-probe-100-per-band.json`. The probe uses
consecutive three-demo windows starting at `lesson_index * 11`, one independent
SHA-256-derived seed per band/lesson, and an independently implemented
4-connected occupancy-boundary oracle. This is a finite rival census, not a
claim of universal rule induction.
