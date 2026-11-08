# 40b155c46f6e — row-majority cleanup

Version 3.0.0. Zero-background grids, height 5..7 and width 7..12, contain 1..3
separated compact active rows of length 3..6. Each active row has one singleton
color and a different repeated majority. The unchanged canonical Racket program
recolors the singleton to its row majority. It is pinned by `RULE_HASH=d149383b47c7`.

Active rows are no longer restricted to odd positions. A three-phase default
curriculum combines an original-size/palette profile with endpoint, length,
third-row and shared-color-role witnesses. Every consecutive three-demo window
is designed to contradict seven declared canonical-perfect rivals; this is a
finite-competitor claim, not universal identification. Overrides, shorter or
reassembled lessons do not inherit that schedule guarantee.

Exact overrides: `grid_h`, `grid_w`, `n_active_rows`, `run_len`. Invalid types,
invalid values, misspellings and retired palette/texture/position controls reject
explicitly. Generated rows in one grid share `run_len`; canonical validation also
accepts lawful mixed-length rows. Normal input support remains bounded to compact
separated singleton-majority rows, not the full Racket input domain.

Tests and Racket-backed audit tooling are under `tests/` and `workspace/`. Review
return `review_response_review-fd6b371d37a717d6.zip` retains measurements and limits.
Approval remains catalog/maintainer-derived; passing tests does not grant it.
