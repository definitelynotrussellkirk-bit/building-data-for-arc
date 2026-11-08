# Working notes: 2d4e8c8fa10e

## Current rule and authority

Treat each cardinally connected magenta (6) component as one object. Preserve a
component only when its complete shape is exactly a solid 2x2 square; erase every
other magenta component. The selected Racket authority was not changed and remains
pinned by `RULE_HASH = "dbcfc990f307"`.

## Current generator decisions

- Version 3.1.0 retains the three-example ordered curriculum: triomino control,
  tetromino control, and 2x2-with-tail control. Every consecutive three scheduled
  examples contains all three controls and a multiple-target example.
- The prior tetromino templates were all 3x2. Retained audit
  `review-7f65e00a26f3126b:v0001` showed that the canonical-fitting rival “keep
  every four-cell component whose bounding-box height is two” therefore survived
  all generated support. Tetromino support now includes both 3x2 and 2x3 shapes.
  Every ordinary tetromino lesson has at least one of each orientation, and a
  one-tetromino override alternates orientation by sample index.
- `keep_size4_height2` is now an executable canonical shortcut, lesson competitor,
  semantic rival, and witness-linked hypothesis. The horizontal-tetromino witness
  is required to refute it.
- The old fixed six-slot fallback assumed all shapes were at most two columns wide.
  It was replaced with deterministic exhaustive placement so the full advertised
  axis cross-product remains constructive after 2x3 shapes were added.
- `seed` and `sample_index` now reject booleans and non-integers; negative sample
  indices are rejected. This closes the three strict-scalar defects found by the
  before battery.

## Reversal retained for provenance

An intermediate source declared `LESSON_SCHEDULE_PERIOD = 3`. The semantic gate
then emitted `declared_period_not_enumerated`; strict after-policy converted that
warning into a failed stage even though its 12/12 production lessons were
identifiable. The declaration was removed, while the deterministic three-step
schedule and exhaustive 2,700-window task-local probe were retained. Evidence:
`checks/after/` (failed intermediate), `checks/final-battery-r2/` (final green battery),
and `checks/repair-probe.json`.

## Evidence and limits

Final generator SHA-256 is
`46c323125e453e9c61f99b5a6f187887ff8c42e5c541f7898af738dac8dac50c`.
The final 12-stage battery is green and the portable task suite passes 25/25.
A 3,600-draw probe found 1,200 tetromino scenes; all 1,200 contained both
orientations and refuted `keep_size4_height2`. A 300-lesson census found no
ambiguity in ordered production lessons against declared rivals. Arbitrary query
rotation is not promised: 400/1,200 diagnostic rotations were ambiguous because
one control can be held out from the ordered three-demo curriculum. Finite declared
rivals do not prove uniqueness against every possible hypothesis. Ordinary lessons
continue to use two distractors to match the canonical profile; exact overrides
cover one through three.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-7f65e00a26f3126b:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `2ddd94f60a64c5e6489859149e73dfcd739dafbdc06e08f4a14a57484a088f89`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved against accepted exact-source repair review-d360af96dfa100cc:v0001 under reviewer-reported policy. The sole orientation-support finding is addressed by2x3 tetromino production, both orientations in ordinary ordered lessons, executable keep_size4_height2 rival and horizontal_tetromino_control witness.25 reported task tests/12-stage battery pass; arbitrary query rotations are explicitly not claimed and their400 ambiguous cases remain evidence. Canonical authority unchanged; original finding/assessment retained. No claim of universal coverage or training admission.

### Assessment or prior finding

## 2d4e8c8fa10e

**A1: Reproduced validator-domain teaching shortcut; audit target left unchanged.** The rival keeps a cardinally connected magenta component exactly when its cell count is four and its bounding-box height is two. It ignores width and solidity. It matches Racket on all three canonical labeled pairs and the three generated schedule profiles tested (seed 123, easy, sample indices 0..2, no overrides).

The generator's `_SHAPES["tetromino"]` templates are all height-three, width-two shapes. Triominos have three cells and square-tail distractors have five; exact squares have four cells and height two. Consequently this shortcut agrees throughout the generator's current shape-template support, including its count/dimension/profile overrides; adding more draws alone cannot refute it. This support claim comes from template inspection, not an exhaustive random census.

A concrete 10-row by 9-column counterexample is the transpose of the generated 9-by-10 tetromino scene at seed 123, index 1, easy. It passes `self_check` and the documented dimensions, colors, component counts, separation and non-square-tetromino grammar. Racket erases both horizontal tetrominos, while the rival retains their eight cells. The query is validator-domain and reference-lawful, but outside current generated tetromino orientation support. This is a distribution/teaching-support gap, not an incorrect label on a sampled production input or a measured ambiguity for current production queries.

Suggested repair: include horizontal non-square tetrominos and schedule at least one demonstration that refutes this rival when those shapes are permitted as queries. Add the rival and an orientation-support regression. If restricting intended task support to vertical tetrominos instead, state that scope explicitly and reconcile the broader validator/rule account.

Source generator SHA-256: `2ddd94f60a64c5e6489859149e73dfcd739dafbdc06e08f4a14a57484a088f89`. Canonical normalized rule SHA-256: `dbcfc990f307839bb7005dbf3305394ae3a1c9627d4d50b47c36b613546b7ff3`; executed rule hash `dbcfc990f307`; exact Racket rule-text SHA-256 `8d443f4f898db02d661fcd8e2a10fe5be5c97617b73c1f164063e78dea714be0`. No unresolved audit index exists for this target, and its notes are a placeholder; no prior return was used as a lead.

Evidence: `checks/audit/2d4e8c8fa10e/comparison.json` contains exact inputs, independent rival outputs, actual Racket outputs, source/rule hashes, self-check results, construction provenance, differing coordinates and command records. `input.json`, `probe.py`, `probe.json`, `probe.log`, `racket.json` and `racket.log` live beside it. Checks: 7/7 Racket executions valid, 7/7 validator inputs accepted; rival agrees on 3/3 generated demos and 3/3 canonical pairs, differs on one validator-domain query at 8 cells. The probe and public `apply` commands both exited 0. Commands and packet-root invocation/runtime-repo cwd are retained in `comparison.json`. No full battery or production census was run.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-7f65e00a26f3126b-v0001/audit_assets.json), manifest SHA-256 `f04b78a47f642aeb3b82ca847fcbcd41fd62eb41b50a565e021c693bd256036f`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `46c323125e453e9c61f99b5a6f187887ff8c42e5c541f7898af738dac8dac50c`.

# Decisions for 2d4e8c8fa10e

## D1 — Use the retained orientation audit as the repair lead

**Prior choice:** all generated tetromino distractors were normalized 3x2 shapes.
The original rationale is not stated in current notes; the code comment indicates
it simplified a six-slot fallback on the minimum 8x9 grid.

**Decision:** accept retained audit `review-7f65e00a26f3126b:v0001` as a concrete,
source-bound lead and reproduce its rival in the current contract.

**Evidence:** the rival `keep_size4_height2` fits all 3 canonical pairs. The
original shape table contains only 3x2 tetrominoes. A lawful horizontal 2x3
counterexample passes `self_check` and disagrees with the selected Racket rule at
four cells. See `checks/repair/height2-counterexample.json`.

## D2 — Expand generated support instead of narrowing the validator

**Alternatives considered:**

1. Restrict `self_check` and documentation to vertical tetrominoes.
2. Add occasional horizontal tetrominoes without guaranteeing a teaching witness.
3. Add both orientations and make the counterexample unavoidable in each ordinary
   tetromino lesson.

**Decision:** option 3. The authority is orientation-invariant, the existing
validator already accepted the horizontal case, and a merely rare counterexample
would leave many lessons shortcut-compatible. Ordinary tetromino lessons have two
distractors and now include both orientations. An exact override with one
tetromino alternates orientation by sample index so both remain constructible.

**Failure mode checked:** 1,200/1,200 ordinary tetromino scenes contained both
2x3 and 3x2 objects and refuted the rival. Single-tetromino exact overrides
produced 27 horizontal and 27 vertical cases in the retained probe.

## D3 — Declare the shortcut as executable semantics

**Decision:** add `keep_size4_height2` to `SEMANTIC_RIVALS`,
`LESSON_COMPETITORS`, and `CANONICAL_SHORTCUTS`; add a
`horizontal_tetromino_control` witness and link it through `WITNESS_RIVALS`.

**Reason:** distribution changes without an executable rival can regress silently.
The declarations make canonical fit, lesson survival, purity, and witness
refutation visible to the standard semantic gate and census.

**Limit:** this finite rival set is not a proof that every alternative rule is
refuted.

## D4 — Preserve the full override cross-product

**Prior choice:** a hand-built six-slot fallback assumed shapes no wider than two
columns.

**Decision:** replace it with deterministic exhaustive use of the existing
backtracking placer. This is narrower than inventing a second placement algorithm
and supports both orientations without reducing any advertised axis domain.

**Evidence:** 486 cross-product calls across two sample indices passed exact
round-trip observation and `self_check`; the standard override stage is green.

## D5 — Enforce strict identity scalar types at the public boundary

**Decision:** validate `seed` and `sample_index` before schedule and RNG setup.
Require literal integers, reject booleans and other scalar types, and require a
non-negative sample index.

**Reason:** Python booleans are integer subclasses, and negative indices silently
selected schedule profiles. The before battery reproduced three invalid
acceptances. Tests cover invalid seed/index types and a negative index.

## D6 — Keep the selected Racket authority unchanged

**Decision:** no rule patch.

**Reason:** the defect was generated teaching support and API validation, not
reference behavior. Current Racket execution, Python mirror, and the exact
counterexample agree. `RULE_HASH` remains `dbcfc990f307`.

## D7 — Retain an ordered three-example curriculum

**Decision:** keep the triomino/tetromino/square-tail three-step schedule and
`EXAMPLES_NEEDED = 3`. Do not claim arbitrary query rotation.

**Evidence:** 2,700 sliding production windows were clear; the 300-lesson census
found no ordered-production ambiguity. Holding out each labelled pair instead
made 400/1,200 rotations ambiguous because the omitted example can be the sole
control for a named shortcut.

**Limitation:** downstream assembly must preserve the intended ordered
three-demonstration policy, or add redundant controls before allowing arbitrary
query positions.

## D8 — Reverse the optional schedule-period declaration

**Intermediate choice:** declare `LESSON_SCHEDULE_PERIOD = 3` to describe the
real schedule.

**Observed failure:** the semantic gate emitted
`declared_period_not_enumerated`; strict after-policy made the otherwise clean
battery fail. The gate cannot consume a separately retained enumeration receipt.

**Final choice:** remove only the optional declaration. Keep the actual schedule,
tests, 2,700-window probe, and diagnostic census. The intermediate failure is
retained in `checks/after/`; the final source is verified in `checks/final-battery-r2/`.

## D9 — Evidence and stopping boundary

The assigned generator has no remaining strict check failure. Ordinary lessons
retain the canonical two-distractor count; exact overrides cover one through
three. No unrelated refactor or authority change was made. The two random audit
targets were investigated and documented only, as required.

## D10 — Native controller-axis family (`review-40f330dbd76de23e`)

**Base decision.** Keep the approved production `generator.py` and canonical
program unchanged. The exact native default is `selection=all_exact_squares`;
its program SHA-256 is
`dbcfc990f307839bb7005dbf3305394ae3a1c9627d4d50b47c36b613546b7ff3`.

**Added branch.** `selection=controller_axis` uses the same generated inputs. It
finds the unique largest non-square color-6 controller, derives its long-axis
orientation and exact row or column, and keeps only exact solid 2×2 color-6
components intersecting that axis. The alternative program SHA-256 is
`60dcab1b418a9492a81c73800551e3eab64b4f7289d158cb8cf372621c6ed59f`.
The two-example minimum presents horizontal and vertical controllers, with both
aligned and off-axis squares, preventing a fixed-orientation or keep-all-squares
shortcut in the declared finite rival set.

**Retained evidence.** The task-local family supports 2–6 demonstrations and
1–4 queries; its four-query bank ends with a 30×30 scene containing eight exact
squares and eight non-square components including the controller. The focused
suite is 4/4 and the full changed-target suite is 29/29. A 40-seed audit covered
80 setting episodes and 240 pairs with matched inputs, distinct setting outputs,
both controller orientations and no query-disagreeing survivor among the
declared finite rivals. Native authoring preflight executed 32 protected-Racket
labels. A separately replayed protected-Racket wrong-intermediate witness uses
the perpendicular midpoint axis and changes eight output cells. Sequential
projection produced 16 one-query views from four episodes and passed first-turn
hidden-field invariance checks.

**Boundary.** This is a reviewer-ready prototype, not owner acceptance or training
admission. The audit is bounded and finite-rival only. Exact-source owner
qualification, fresh replay and acceptance remain mandatory.
