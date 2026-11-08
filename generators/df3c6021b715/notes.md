# Working notes: df3c6021b715

## 2026-10-19 review — strict API repair and parametric prototype

- Used `review-463a8c78e1056098:v0001` as the repair lead and
  `review-fd6ce8c89abe4417:v0001` as the retained audit lead; all current
  claims below were remeasured against this packet's selected source.
- The pre-change battery retained one blocking `strict-scalar` finding:
  unsupported `difficulty` values were accepted.  A first repair exposed the
  rest of the same boundary—boolean/float/string seeds and sample indices, plus
  negative sample indices—and those exact cases were converted into regression
  tests before the final minimal validation was added.
- Final generator SHA-256:
  `5433fc14947370131cdb4f13b51c1bdf45ac15fe95590d1b89f7e90f7c0c9966`.
  The selected Racket authority and `RULE_HASH = 77666531c7cb` were unchanged.
- Final evidence: all 12 after-battery stages green; 81/81 portable task tests
  pass; 300/300 lessons and 1,200/1,200 held-out query rotations have no
  ambiguity against the declared rivals, with 1,107 unique inputs.

### Proposed original-family parameter (not selected production code)

`workspace/parametric/` contains a runnable episode-level
`partition_axis ∈ {horizontal, vertical}` prototype.  `horizontal` is the
canonical default; `vertical` is its 90-degree relational analogue.  Inputs
contain exactly two distinct interior dots, one in each horizontal half and one
in each vertical half, so the same input is lawful under either setting.  Each
materialized episode has three demonstrations and one query.  The protected
Racket verifier checked 8/8 pairs and confirmed that all 6 demonstrations and
both queries distinguish the selected axis from the rival setting.  Public
artifacts omit the hidden parameter, program source, and query answer.

This prototype is intentionally isolated from `generate()`, approval, and the
canonical execution path.  Its finite two-rule distinction is evidence for the
proposed parameter only; it is not a proof of unique induction against all
possible rules.  Promoting it would require a separate source/variant review
and a production sampler decision.

## 2026-10-05 review repair

- Replaced the v2 sampler's partially effective/coercive controls and
  out-of-domain degenerates with seven exact integer axes.  `observe_overrides`
  reconstructs every advertised value from pixels; unknown and non-integer
  values are rejected.
- Corrected the half boundary to the selected Racket DSL's integer division:
  `mid = h // 2`.  On height 11, row 5 belongs to the lower half.
- Added a deterministic four-profile curriculum: two 10×10 morphology anchors
  plus two broad-height profiles.  Three executable competitors cover the
  strongest canonical shortcuts: fixed dot rows 2/7, ascending colour ownership,
  and a fixed side-colour transition at row 5.
- Added source-bound tests under `tests/test_generator.py` for canonical parity,
  malformed grids, exact overrides, even/odd split adjacency, declared rivals,
  every cyclic schedule start, and every query rotation.
- Synchronized the active base record's `racket_target.target_code` to the
  canonical selected program.  The archival `raw_code` is intentionally
  preserved as provenance; the canonical program itself was not changed.

## Historical 2026-10-05 measured evidence

- Generator SHA-256:
  `160eeece23f77af8916ebcdd18f58d08f703b3d868fc134bca5f5e278f54cf0a`.
- Full after battery: 12/12 green.
- Task-local tests: 56/56 passed.
- Override replay: 61,740/61,740 accepted, zero findings or warnings.
- Lesson census: 300/300 lessons and 1,200/1,200 query rotations identifiable
  against all declared competitors; 1,107 unique inputs.

The finite competitor set is not a proof of universal identifiability.  Default
teaching profiles intentionally avoid heights 10 and 11 in the broad profiles
because both share the canonical row-5 split, while exact overrides still cover
both heights and the complete advertised domain.
## Historical 2026-10-05 reviewer considerations

Source SHA-256: `160eeece23f77af8916ebcdd18f58d08f703b3d868fc134bca5f5e278f54cf0a`.

# DECISIONS — df3c6021b715

## Intended outcome and success criteria

The repair should generate only lawful two-dot inputs, make every advertised
control exact and replayable, preserve the selected Racket program as label
authority, and assemble three-demo lessons that distinguish the strongest rules
that fit all canonical demonstrations.  Success required the full battery,
source-bound tests, required query rotations, and a 100-lessons-per-band census.

## D1: Domain and dimensions

**Decision.** Use rectangular grids with independently controlled `grid_h` and
`grid_w`, each in 8..18.  Exactly two nonzero interior cells are required, with
one row `< h // 2` and one row `>= h // 2`.

**Why.** The old implementation coupled width bounds to the height difficulty
range and advertised 6..18 even though canonical-like support and teaching
quality were weak at the edge.  The chosen range preserves meaningful frame
interiors, supports odd/even midpoint probes, and passes strict/domain checks.

**Rejected alternatives.** Keeping 6–7 dimensions would leave very little space
between frame rows and borders.  Coupling width to height was rejected because
it makes `grid_w` non-exact and hides rectangular cases.

## D2: Ordered colour pair

**Decision.** Encode upper/lower colours as one exact integer `color_pair` in
0..71 over all ordered distinct pairs from 1..9.

**Why.** Separate `dot1_color` and `dot2_color` overrides previously coerced an
equal pair into another value, so requested values were not observable.  A
single ordered-pair index makes all 72 legal assignments constructive and lets
the observer recover the exact request.

**Rejected alternatives.** Two independent colour axes plus an incompatibility
list would be larger, slower to replay, and still require special handling for
72 legal versus 9 illegal combinations.  Palette-kind labels were removed
because they did not define an exact pixel contract and did not teach the rule.

## D3: Row and column positions

**Decision.** Use `upper_row_slot` and `lower_row_slot` in 0..2 and
`upper_col_slot` and `lower_col_slot` in 0..4.  Slots are deterministically
mapped to spread positions in the legal interval; the inner row slots include
the rows directly adjacent to the split.

**Why.** This gives compact exact controls while covering outer, middle, and
split-adjacent row behavior plus five horizontal positions.  It fixes the old
lower-row picker, which skipped the first legal lower row and therefore could
not construct split-adjacent dots.

**Rejected alternatives.** Raw row/column coordinates would require complex
height/width-dependent incompatibilities.  Free-form position biases
(`left_aligned`, `diagonal`, and so on) were not exact enough for override
verification and were not semantically relevant.

## D4: Integer midpoint semantics

**Decision.** Every Python-side boundary uses `h // 2`, matching integer
truncation in the selected Racket DSL.

**Why.** On height 11, the authority puts row 5 in the lower half.  A float or
ceiling interpretation silently relabels that row, corrupting validation,
observation, the Python oracle, and witness scoring.  The 11×11 counterexample
is retained under `checks/semantic-counterexample-*`.

**Rejected alternatives.** Avoiding odd heights would hide the mismatch rather
than repair it.  Changing the Racket rule was unjustified because canonical
outputs and the selected authority consistently use integer division.

## D5: No degenerate textures

**Decision.** Remove `same_color`, `same_position`, `no_dots`, and all alias or
boolean axes that generate no pixel effect.  `INCOMPATIBLE_OVERRIDE_COMBINATIONS`
is empty because every assignment in the seven-axis product is constructive.

**Why.** Those textures violate the stated task domain and make training labels
irrelevant or undefined.  Degenerate examples belong in validator tests, not the
production sampler.

**Rejected alternatives.** Retaining them behind a `texture` flag was rejected
because the battery treats advertised axes as part of the production contract;
calling an out-of-domain sample a “degenerate” does not make it useful training
data.

## D6: Four-profile teaching schedule

**Decision.** Cycle deterministically through:

1. `canonical_anchor`: 10×10, middle dot rows, ascending colours.
2. `reversed_outer_rows`: broad non-10/11 height, outer rows, reversed colours.
3. `reversed_inner_rows`: 10×10, noncanonical dot rows, reversed colours.
4. `reversed_cross_rows`: broad non-10/11 height, cross rows, reversed colours.

Each lesson uses three demonstrations and one query (`EXAMPLES_NEEDED = 3`).
Exact overrides take precedence over profile defaults.

**Why.** Two exact-morphology profiles keep every difficulty band's profile
floor comfortably above zero.  The reversed/noncanonical profiles guarantee
that each three-demo window rejects fixed rows 2/7 and ascending colour order.
The broad profiles also reject a fixed transition at row 5.  Excluding heights
10 and 11 only from broad defaults avoids spending a purported split witness on
a height that still transitions at row 5; exact overrides continue to cover
both heights.

**Rejected alternatives.** Pure random sampling could leave a complete lesson
ambiguous even when witness frequency looked good in aggregate.  Four canonical
10×10 profiles preserve all three shortcuts.  Four broad profiles failed the
canonical profile-floor policy.  A single canonical profile plus three broad
profiles produced only 20% support in one measured anchor, below the required
clean floor; the second 10×10 teaching profile repaired that without restoring
the shortcuts.

## D7: Executable rivals and witnesses

**Decision.** Declare and execute three canonical competitors:

- `fixed_dot_rows_2_7`
- `sort_colors_ascending`
- `fixed_split_row_5`

Each has a real Python output function, a witness predicate, and a mapping from
witness to rival.  `lesson_identifiable` rejects a lesson if any declared rival
fits all demonstrations.

**Why.** All three rivals fit every canonical pair.  Executable outputs let the
semantic gate verify actual disagreement rather than trust a descriptive flag.
The final gate measured 60/60 correct disagreement claims per rival; the larger
census found no surviving declared rival in 300 lessons or 1,200 rotations.

**Limitation.** This finite set is a testable contract, not a proof against every
possible program.  Future agents should add a rival only with an executable
output and a retained exact counterexample.

## D8: Validation, observer, and Python oracle

**Decision.** `self_check` diagnoses malformed grids and the broad lawful
two-dot domain; `strict_canonical_like` delegates to it.  `observe_overrides`
recovers the exact sampler lattice and raises on lawful off-lattice grids.  The
Python oracle is independent support code for tests and rival scoring; Racket
remains label authority.

**Why.** Separating broad domain validity from exact sampler observability avoids
mistaking an off-lattice but lawful grid for invalid.  Strict type checks reject
booleans, floats, strings, unknown keys, and out-of-range values instead of
silently coercing them.

## D9: Authority synchronization

**Decision.** Leave `repo/shared/data/canonical/puzzles.jsonl` untouched and
synchronize only `racket_target.target_code` in the assigned base solution to
the canonical selected program.  Preserve `raw_code` unchanged.

**Why.** The pre-sync battery had 10/12 green; the only two failures were text
synchronization checks, while execution parity already passed.  The base path is
explicitly assignment-bound and patchable.  Treating `raw_code` as archival
provenance preserves lineage while making the active executable source exact.

**Rejected alternatives.** Editing the canonical rule had no semantic basis.
Rewriting `raw_code` would erase provenance.  Ignoring the failures would leave
the selected active source ambiguous to future tools.

## D10: Tests and retained evidence

**Decision.** Add 56 portable task-local tests and retain real red/green
iterations.  Keep large override reports losslessly gzip-compressed with
original size/SHA/restoration commands in
`checks/LARGE-EVIDENCE-MANIFEST.json`.

**Why.** The tests cover behavior that generic batteries cannot cheaply exhaust:
every cyclic schedule start, all four held-out query positions, odd/even split
adjacency, exact override reconstruction, malformed mutations, and canonical
parity.  Compression preserves replay evidence while respecting the return's
25 MiB expanded-evidence budget.
## Current reviewer considerations

Source SHA-256: `5433fc14947370131cdb4f13b51c1bdf45ac15fe95590d1b89f7e90f7c0c9966`.

# Decisions — review-92b732083ae35fd7

## D1 — Preserve the selected rule and distribution

**Choice.** Keep the canonical Racket program, `RULE_HASH = 77666531c7cb`, all
seven advertised generation axes, and the four-profile teaching schedule.
Change only validation at the public `generate()` boundary.

**Rationale.** The baseline had 11/12 green stages; rule smoke, authority sync,
profile floor, overrides, semantic witnesses, diversity, and grammar were
already sound.  The sole reproducible defect was accepted invalid scalar input.

**Alternatives rejected.** Changing the Racket rule or resampling distribution
would address no measured failure and risk introducing a new shortcut.  Quietly
coercing values was rejected because booleans, floats, strings, and negative
indices create aliases that are absent from the declared contract.

**Probe and failure mode.** Focused tests first demonstrated that invalid values
did not raise.  The intermediate difficulty-only repair then let defect lint
identify the remaining seed/sample-index cases.  The final implementation
requires exact `int` type for seeds and indices and nonnegative indices.  A
future API decision could separately forbid negative integer seeds; this review
did not do so because they are deterministic and were not reported invalid.

## D2 — Add regression coverage at the source of the defect

**Choice.** Add `tests/test_review_regressions.py` with 17 explicit bad-call
cases rather than relying only on generic battery coverage.

**Rationale.** The test names describe the public contract and fail directly if
coercive behavior returns.  They also distinguish type errors from schedule
logic, making future failures cheaper to diagnose.

**Alternatives rejected.** A single detector-only assertion would be less local
and could regress if the shared linter changed.  Testing implementation details
inside `gen_ctx` would not prove this generator's public behavior.

**Limit.** These cases cover the shared detector's current scalar families; they
do not define every future Python object that should be rejected.

## D3 — Use one episode-level original-family parameter

**Choice.** Prototype `partition_axis ∈ {horizontal, vertical}`.  Horizontal is
the canonical default; vertical rotates the relationship while preserving the
two colored singleton roles and frame-construction reasoning.

**Rationale.** This is a small, compositional parameter rather than a palette or
layout alias.  A solver must infer which spatial partition governs the episode.
Both rules are short Racket programs and share one lawful input grammar.

**Alternatives rejected.** Color-order parameters would encourage numerical
color shortcuts.  Moving frame rows or dot columns changes nuisance geometry,
not the rule.  Combining axis with further parameters was deferred to keep the
first extension identifiable and auditable.

**Failure mode and limit.** If demonstrations happen to agree under both axes,
the query is underdetermined even with correct labels.  The prototype therefore
rejects any pair that does not distinguish the selected rule from its rival.
This two-rule test is not universal identifiability.

## D4 — Constrain parametric inputs symmetrically

**Choice.** Require two distinct interior dots with one dot in each horizontal
half and one in each vertical half; choose the parameter once per episode; emit
three demonstrations and one query.

**Rationale.** The same input is valid under both rules, preventing the hidden
setting from leaking through legality.  Three demonstrations match the selected
canonical lesson policy and provide repeated relational evidence.

**Alternatives rejected.** Separate input distributions per setting would make
axis prediction possible from morphology alone.  One demonstration is fragile;
more than three adds cost without evidence of need for this bounded prototype.

**Probe.** `workspace/parametric/verify.py` executes both Racket rules on every
materialized pair and requires selected/alternative disagreement.  Final counts:
8/8 Racket-labelled pairs, 6/6 demonstrations, and 2/2 queries distinguished.

## D5 — Keep the parameter outside production

**Choice.** Store the prototype, verifier, Racket programs, and materialized
examples only under `workspace/parametric/`.

**Rationale.** The assignment asks for assessment and a runnable proposal, not
unreviewed source promotion.  Keeping it isolated preserves current approval,
rule authority, and training behavior.

**Alternative rejected.** Adding `partition_axis` to `AXES` would silently make
a proposed rule variant part of the selected generator and invalidate existing
approval evidence.

## D6 — Retain failed evidence and use the final-source census

**Choice.** Preserve the baseline failure and intermediate failure, then run a
fresh final battery, portable task tests, protected parametric verification, and
100 lessons per difficulty band with required query rotations.

**Rationale.** This records the actual root-cause sequence and binds successful
claims to the final generator hash.  The 300-lesson census is warranted because
three plausible rivals fit all canonical pairs.

**Limit.** The random census covers all requested bands and query rotations but
is not an exhaustive proof over all seeds or undeclared rivals.

## D7 — Audit without editing peer targets

**Choice.** Reproduce and report defects for `b7ff231aab1a` and
`2a10fa5d18dc`; make no peer-source changes.

**Rationale.** Audit intake is evidence-only.  The first target has strong task
and semantic tests but accepts invalid call scalars.  The second has a broader
contract failure: ignored/contradictory controls, invalid degenerate outputs,
no task tests, and no semantic contract.

## D8 — Record the post-repair solve as exposed

**Choice.** Mark earlier rule exposure `yes` and reference consultation during
the solve `no`.

**Rationale.** The solve happened after generator review, so calling it blind
would be false.  During the solve phase only the visible challenge and local
Python implementation were used.
