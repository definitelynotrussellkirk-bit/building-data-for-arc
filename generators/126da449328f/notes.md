# Working notes: 126da449328f

## Current rule and domain

Each nonzero singleton seed emits a same-color straight ray through its nearest border.  Equal distances use the selected Racket authority's total order **top, bottom, left, right**.  Ordinary generated inputs are rectangular 7–9 by 7–9 grids with background 0, three or four distinct interior seeds, pairwise-disjoint selected rays, and at least three selected directions.  `RULE_HASH = f5d1690cbbbb`; neither the canonical row nor the Racket authority was changed in this review.

The inherited six-profile curriculum came from prior return `external-local-random:a2c26df2299b`, used as a lead rather than as a fresh measurement.  Profiles repeat by `sample_index % 6`: unique minima, top-over-side, bottom-over-side, top-over-bottom, left-over-right, and mixed priority.  A production lesson has six ordered demonstrations followed by one query, so every demonstration window contains all six profiles.

## 2026-10-11 review decisions

The pinned baseline accepted coercible or invalid public controls.  `schedule_profile` and `generate` accepted Boolean, float, string, or negative sample indices; `generate` also accepted non-integer seeds and coercible values for integer overrides.  The current source validates the public boundary before constructing `GenCtx`: seeds must be literal integers, sample indices must be nonnegative literal integers, difficulties must be one of the declared bands, unknown axes are rejected, and each integer override must be a literal in-range integer.  `_draw_axis_int` now uses strict integer draws for scheduled and exact values.  This is deliberately a validation-only repair: `checks/strict-controls/valid_output_parity.json` records 252/252 valid calls unchanged between baseline hash `e64aeb744a787f815eda38f710ca80e86bf2e88a95d74e65e9253403ca1a03f1` and final generator hash `2be6f0000df78621d4bdd5f438fc151ac4ff1825f2c076cf674e82dc2cde7665`.

The strongest newly named canonical-compatible shortcut is `right_over_left_ties`: apply the intended nearest-border rule, but choose right instead of left on a left/right tie.  It agrees with every labeled canonical pair, because those pairs do not isolate this branch.  Generated profile `left_over_right` refutes it.  The exact retained witness is `counterexamples/right_over_left_tie.json` (seed 126449, sample index 4, medium; the color-4 seed at `(4, 3)` in a 9×7 grid is tied left/right).

Focused regressions are in `tests/test_strict_controls.py`.  They cover invalid sample indices, invalid seeds, coercible integer overrides, canonical fit of the new shortcut, and a generated counterexample.  Final task-local result: 16 passed.  The full final battery is 12/12 green.

## Lesson evidence and limits

The final 100-lessons-per-band census materialized 300/300 production lessons, 2,100 labeled pairs, and 2,092 unique input hashes with zero production ambiguities against the declared rivals.  Arbitrary query rotation is **not** claimed: holding out every pair produced 252 ambiguous rotations out of 2,100, with 1,500 rotation hook warnings.  This is expected for the intentionally ordered six-demonstration curriculum when the unique witness for a branch is removed.  `checks/lesson-census-diagnostic.json` therefore records production `no_ambiguity_found` and rotation `ambiguous` under diagnostic rotation policy.

Finite declared-rival checks do not prove universal identifiability.  The generator deliberately teaches the total tie order through pairwise witnesses but does not schedule three- or four-way ties.  Grid size, seed count, disjoint rays, distinct colors, and the six-example ordering are task-local grammar restrictions, not claims about every lawful input accepted by the Racket rule.  Re-run the focused tests, full battery, and lesson census after changing controls, profiles, lesson order, or rival declarations.
## Current reviewer considerations

Source SHA-256: `2be6f0000df78621d4bdd5f438fc151ac4ff1825f2c076cf674e82dc2cde7665`.

# Decisions: 126da449328f

## D1 — Preserve the selected rule and valid distribution

**Original choice.** The pinned baseline already implemented the selected Racket behavior: nearest-border rays with tie priority top, bottom, left, right.  Prior return `external-local-random:a2c26df2299b` was consulted as a lead for the six-profile curriculum and the known absence of deliberate multiway ties; its claims were not reused as current measurements.

**Decision.** Keep the canonical row and Racket authority unchanged and repair only the Python generator contract.  The source remains bound to `RULE_HASH=f5d1690cbbbb`.

**Alternatives rejected.** Rewriting the rule, changing the seed grammar, or resampling valid calls would have expanded scope without addressing the measured failure.  A 252-case before/after parity probe showed that boundary validation could be fixed with 0 valid-output changes.

**Failure mode and limit.** The task-local grammar is narrower than every input on which the Racket program can execute.  This return claims generator correctness within the declared 7–9 by 7–9, 3–4-seed domain, not universal rule coverage.

## D2 — Reject coercion at the public boundary

**Observed input choice.** Baseline code delegated controls to coercive helpers.  `sample_index` accepted `True`, `False`, `1.0`, `"1"`, and `-1`; seeds and integer overrides also accepted coercible non-integers.

**Decision.** Validate `seed`, `sample_index`, `difficulty`, override names, override types, and override ranges before creating `GenCtx`.  Use `type(value) is int` so Boolean values are rejected despite `bool` subclassing `int`.  Use `draw_int_strict` for scheduled or exact integer-axis values.

**Alternatives rejected.** Applying `int(value)` or relying only on range checks would preserve the bug.  Fixing only the five values named by defect lint would leave `grid_h=7.0`, `grid_h="7"`, and analogous override cases accepted.

**Probe and evidence.** `tests/test_strict_controls.py` was written red first.  The initial 15 failures are retained in `checks/task-tests-red/`; final 15 control tests and the rival test pass in `checks/task-tests-final/`.  Valid parity is in `checks/strict-controls/valid_output_parity.json`.

## D3 — Name the strongest canonical-compatible rival

**Original rationale.** Existing competitors covered horizontal-first ties, unchanged ties, one-step extension, and all-horizontal/all-vertical behavior.  The canonical examples demonstrate a top/right tie but do not isolate the left/right branch.

**Decision.** Add `right_over_left_ties`: nearest-border extension with priority top, bottom, right, left.  Include it in both `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, and bind it to the `left_over_right` witness profile.

**Alternatives considered.** A global right-first rule is weaker because canonical top/right evidence refutes it.  “Horizontal first” was already declared.  Reversing only left/right is the smallest plausible branch error that still fits every labeled canonical pair.

**Exact witness.** Seed `126449`, sample index `4`, difficulty `medium` produces a 9×7 grid with color 4 at `(4,3)`, equidistant from left and right.  The intended output extends left; the rival extends right.  Six cells differ.  Full input and both outputs are in `repo/generators/126da449328f/counterexamples/right_over_left_tie.json`.

## D4 — Retain an ordered six-demonstration curriculum

**Original choice.** The generator schedules six profiles by `sample_index % 6`; every six consecutive scenes contain one of each profile.  Lessons use six ordered demonstrations and a seventh query.

**Decision.** Preserve that assembly.  It is economical and the final production census found no declared-rival ambiguity in 300/300 lessons.

**Alternative rejected.** Claiming arbitrary query placement is unsupported.  Holding out each of the 2,100 materialized pairs left 252 rotations ambiguous and produced 1,500 hook warnings, usually because the only witness for a branch became the query.

**Policy.** Rotation evidence is diagnostic, not a production gate.  Downstream exporters must retain the six-demo order and query position.  A future requirement for arbitrary rotations would require redundant witnesses or more demonstrations, followed by a fresh required-rotation census.

## D5 — Keep pairwise tie teaching; document multiway absence

**Decision.** Continue to establish the total priority through pairwise profiles rather than add three- or four-way center ties now.  The pairwise schedule is sufficient against the declared rivals and keeps rays disjoint with three or four seeds.

**Risk.** A learner could still adopt an undeclared behavior that agrees on all scheduled pairwise cases but differs on a multiway tie.  The finite census cannot rule this out.  Multiway coverage remains a documented limitation, not silently claimed support.

## D6 — Preserve failures and separate audits

Both red TDD runs, the before battery failure, the required-rotation ambiguity, and the initially interrupted audit self-check are retained.  Audit targets `98e5564fbf8a` and `e58b545527d3` were not edited; their source-bound defects are documented in `AUDIT.md`.  No audit result is presented as approval or as part of the selected generator repair.
