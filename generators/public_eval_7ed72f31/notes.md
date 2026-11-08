# Current decision — public_eval_7ed72f31

Authored canonical rule: background is the unique most frequent color. Recover
8-connected multicolor foreground groups; red (2) is the local marker. A red
singleton is a half-turn center; a complete red horizontal/vertical segment is
an infinite reflection axis. Copy that group's nonred cells into background,
retaining original content. Association is local, not global by source color.
The general Racket implementation reproduces all two train labels and both
provided test answers (4/4 protected original labels).

`line_action=reflect` exactly equals reference.rkt and canonical.rkt.
`half_turn` instead turns each line-attached source by 180 degrees about the
marker segment midpoint; singleton behavior stays unchanged. Doubled centers
handle both odd and even marker lengths using integer cell coordinates.
A: recover each local marker geometry and its source cells. B: consume their
relative coordinates to place each copy. A source-bound counterfactual replaces
the marker midpoint with the source bounding-box midpoint; protected Racket
changes 82 cells on the retained exact 30×30 alternate-setting case.

Sampler: three or four local groups ordinarily and nine in the 30×30 stress
scene, with points plus horizontal and vertical segments, variable lengths,
translated/rotated placements, repeated colors across separate groups,
diagonal-only contacts, and sources extending past line endpoints. It rejects
merged input groups and either-setting collisions, with a 256-attempt bound.
Two same-colored groups teach local rather than global-color association.
The source grammar is deliberately collision-free and uses complete straight
markers; arbitrary malformed markers, uncertain backgrounds and overlapping
copy targets are outside that grammar. Canonical copying clips at canvas edges
and preserves nonbackground observations; sampling does not use clipping to
hide evidence. No stored official answers or data files are runtime dependencies.

All 26 focused tests pass. A 64-seed audit covers both settings and every count
2..6: 640 nested lesson views, 5,120 pair exposures. Twelve Python rival rules
have zero query-changing survivors; this finite screen is not a uniqueness proof.
A protected extra audit verifies 40 generated labels at six demonstrations,
then two causal labels; a separate process replays both causal labels.
All original labels and authoring preflight pass. Sixteen saved one-query views
pass exact visible-byte/hash checks and private-field mutation/positive controls.

The explicit presentation seed randomizes the complete private four-query bank
before selecting a single visible query. Directory listings, permutation maps,
settings, programs and query answers stay with the controller. Public IDs hash
only the exact current view. Demonstration and query prefixes are independent.

A copied-runtime smoke exercised ordinary and native generation for both
families with ten protected labels total, without the original parent data or
predecessor Python imports. Final self-review was by the author (no independent
reviewer tool). Registration, owner native qualification/acceptance and any
training-admission decision remain pending. No shared source or authority changed.
