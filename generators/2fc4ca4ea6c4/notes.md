# Working notes: 2fc4ca4ea6c4

Current source is generator version 2.1.0. The ordinary generator's advertised override contract was repaired: `grid_h`, `grid_w`, `run_rows`, `n_distinct_colors`, and `texture` now reject unknown/out-of-range values consistently, and regular draws deliberately teach both singleton identity and longer odd-run collapse. The exact canonical midpoint rule remains the default.

The native parametric family adds `completion_mode=connect_aligned`: first collapse every horizontal run to its midpoint, then connect exactly two same-colored midpoint cells aligned in a column only through zero cells. Its matched-input lesson bank supports 2–6 demonstrations and 1–4 queries, retains four distinct sequential queries, and includes a substantive 30×30 boundary/quadrant stress case.

Adversarial review found that early lessons did not distinguish a connector that ignored blockers or one that connected three-or-more endpoints. The lesson constructor now includes a blocked two-endpoint case and a three-endpoint case; retained regressions and the bounded audit require both shortcuts to fail on the two-demo minimum and on queries.

Current reviewer evidence: 48 focused task checks pass; protected authoring preflight passes with 32 Racket evaluations; the protected skip-A witness replays; 16 single-query public projections and 24 private-field invariance checks pass; and the cross-family independent-oracle sweep covers 512 seeds. These are finite reviewer checks, not owner acceptance or training admission. Next owner action is exact-source native qualification and fresh acceptance after integration.
