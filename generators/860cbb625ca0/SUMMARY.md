# 860cbb625ca0

Canonical task: a left template panel and right board are separated by a
full-height color-9 divider; the output reports zero-as-wildcard template-match
counts by board start row.  The selected canonical exact-matching program is
unchanged.

The repaired production generator is version `1.3.1`.  It now implements its
published grid-size, palette, matching-row, placement, color-count and density
controls, rejects incompatible/unobservable requests, and no longer anchors all
matches to one fixed row.

The reviewer-ready native family under `workspace/parametric/` is version
`1.1.0` and selects exact, rotational or full-dihedral matching once per
episode.  It supports 2–6 demonstrations and exactly four distinct queries,
includes a substantive 30×30 query, records the concrete orientation
intermediate and named shortcut attacks, derives labels through protected
Racket, and keeps public/private sequential projections separate.

Kind: `per_puzzle`.  Base generator: `1.3.1`.  Parametric family: `1.1.0`.
Owner source review, fresh native qualification/acceptance and training
admission remain pending.
