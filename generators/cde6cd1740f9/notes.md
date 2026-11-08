# Current notes: cde6cd1740f9, version 4.2.0

Generator SHA-256: `66c20ab0c44e2199caf1664e2b994fa55462fe3383efcb6addc2085b8c7fbbff`.
Selected rule: `027335bb451f`; canonical program SHA-256:
`1eabf7f4ae2d7acbaa8ba9db677c140a76bfabce59d672ea30d1ba06cbd3fae5`.
The selected Racket authority, canonical examples, catalog and approval state
are unchanged in review `review-754f4d9eaf06696d`.

## Intended rule and domain

Each active input column contains `k²` colored cells, for `k` equal to 2 or 3.
Read distinct colors from bottom to top. Their exact counts allocate complete
consecutive layers of widths `2k−1, 2k−3, …, 1`. Move these layers to the grid
bottom, centered on the same source column. Source row positions are discarded;
color multiplicity and order are preserved. Multiple pyramids have disjoint,
on-canvas output footprints. Oracle executability alone is not domain validity.

## Current distribution and lesson decisions

- The five exact controls remain `profile`, `structure`, `active_columns`,
  `primary_color` and `layout_shift`. Profiles and structures are independent.
- Structures now include `mixed_k3_k2_8_1`: the three-layer column uses primary
  on its five- and three-cell layers and secondary on its apex. Existing
  `mixed_k3_k2` retains the complementary 5+4 grouping. Both default to two
  active columns, and lawful one-/two-column overrides remain supported.
- The 20-state schedule enumerates `(PROFILES[i % 4], STRUCTURES[i % 5])`.
  `EXAMPLES_NEEDED = 9`: nine consecutive demonstrations precede one query.
  Each ten-pair window contains two of every structure; removing any one query
  preserves both two-color grouping witnesses. Difficulty offsets retain this
  coverage. Smaller or externally assembled lessons are not guaranteed.
- Seeds must be literal integers; indexes literal nonnegative integers. Exact
  integer controls reject booleans, floats and strings rather than coercing them.
- Eight distinct semantic competitors include `ignore_grouped_color_counts`.
  Only `canvas_template` and that count-ignoring rival are declared as canonical
  shortcuts: both actually fit all four unique canonical pairs. Other rivals
  remain semantic negatives without a false canonical-fit claim.

## Reversed choices and evidence

Version 4.1.0 generated only the 5+4 two-color grouping. A rival assigning one
layer per distinct color, then repeating the final color, fit 4/4 unique
canonical pairs and 24/24 measured ordinary baseline draws. The unresolved
`review-40d2bd8fd0adb4ae:v0001` finding was therefore reproduced. Version 4.2.0
adds ordinary 8+1 cases, the named rival, a minimal counterexample and regression
tests. `counterexamples/count_partition_8_1.json` and the reusable
`workspace/probe_count_partitions.py` preserve the distinction. Both groupings
occur in each band in the 60-draw after probe; the rival fails 12/60 draws.

The prior 16-state/eight-demonstration schedule was replaced to keep two copies
of each of five structures in every ten-pair window. The existing canvas rival
remains tested. `counterexamples/canvas_template_cross_canvas.json` was rebound
to an actual final-source draw; its earlier bytes are retained in the return.
Portable tests now consistently use the public selected-generator and canonical
helpers. The historical portability audit is a lead, not a newly reproduced
failure against this baseline. No review-index status was edited.

## Current evidence and limits

The source-bound return retains `checks/after/result.json` (12/12 battery stages),
`checks/task-tests/result.json` (52/52 tests), before failures, and exact
Racket-labelled probes. The random census materialized 300 lessons and 3,000
query rotations with zero declared-rival ambiguity or errors; its 2,999 unique
inputs are counted separately from overlapping windows. The fixed-seed census
covered all 20 starts in three bands: 60 lessons, 600 rotations, 87 unique inputs,
also with no ambiguity. Full reports are retained losslessly as gzip evidence.
These are finite checks against named rivals, not universal induction proofs.

`workspace/parametric/` contains a **proposed prototype**. One episode-level
`base_edge` parameter selects bottom (byte-identical canonical program) or top
(a single row-placement edit). Both retain source column roles, count partitions
and color order; every answer uses Racket. Two retained episodes distinguish the
alternate setting on all nine demos; ten focused prototype tests pass. Wider
production sampling and variant approval remain separate work.

The task-local after gates have no remaining failures. The separate repository
suite has 19 failures, 995 passes and three optional-Torch skips; exact traces
and measured triage are in the return. Shared files were not modified. The
post-repair solve passed 9/9 visible examples with prior exposure declared;
hidden-query correctness remains unknown. Audit and training approval decisions
belong to the maintainer, not these measurements.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-40d2bd8fd0adb4ae:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `2d1797e25875f199afd1e28c88efadb3c974827bce9792e09361120fa6b6ede4`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit resolution of old source 2d1797e25875f199afd1e28c88efadb3c974827bce9792e09361120fa6b6ede4 on accepted current 66c20ab0c44e2199caf1664e2b994fa55462fe3383efcb6addc2085b8c7fbbff. Ordinary mixed_k3_k2_8_1 support, an executable count-ignoring rival and generated Racket witness now distinguish the missing partition. Reported65 Racket probe inputs and300 lessons/3000 rotations plus60 fixed-period lessons/600 rotations cover the promised nine-demo lesson policy; smaller lessons remain limited. No owner rerun.

### Assessment or prior finding

## cde6cd1740f9

**Finding: the generated curriculum never requires individual color counts to determine grouped layers.** An undeclared rival uses the total number of colored cells to choose `k`, reads distinct colors bottom-to-top, assigns one layer to each distinct color, and repeats the final color until there are `k` layers. It matches **4/4 unique canonical labelled pairs and 8/8 ordinary generated inputs** under the actual public Racket rule. A strict, validator-accepted handmade witness refutes it.

Audited source: generator v4.1.0, SHA-256 `2d1797e25875f199afd1e28c88efadb3c974827bce9792e09361120fa6b6ede4`; executed rule hash `027335bb451f`; exact selected rule text SHA-256 `2a8d528c56c6e5a7b0c26758432f172990c2accd208f9d66d23c6eae6740f967`. All three public receipts independently report the audited generator SHA and selected rule hash; [compare.py](checks/audit/cde6cd1740f9/compare.py) asserts those identities. The command recorder's generic `source_before/source_after` field stamps the main repair task, so the audit identity is explicitly pinned in every audit command's note and in the task-specific evidence.

**Why the shortcut survives.** `_column_specs` emits first-column layer colors only as `(p,p)`, `(p,p,p)`, `(p,s,t)`, or `(p,s,s)`. Its optional second column is always `(t,t)`. Therefore all generated two-color three-layer pyramids have the sole partition `5+4`, assigning one bottom layer to the first color and two upper layers to the second. The complete-layer partition `8+1`, assigning two bottom layers to the first color and the top layer to the second, is never generated. Independent canvas/structure scheduling does not vary this choice. This structural argument concerns current sampler support; the measured public-Racket sample is the bounded set above, not an exhaustive runtime census.

**Exact witness.** [witness-input.json](checks/audit/cde6cd1740f9/witness-input.json) contains one bare input grid, dimensions 16×13. Every cell is zero except column 6: row 1 has color 5; rows 4–11 have color 2 (zero-based coordinates). The column contains nine colored cells, counts `{2:8,5:1}`, and distinct order `(2,5)` bottom-to-top. Both `self_check` and `strict_canonical_like` return `[]`; observed axes are `profile=16x13`, `structure=mixed_k3_k2`, `active_columns=1`, `primary_color=2`, `layout_shift=1`. Its scattered row positions came from the generated baseline seed 73, sample index 0, difficulty medium, overrides `{profile:16x13, structure:mixed_k3_k2, active_columns:1, primary_color:2, layout_shift:1}`, then its color counts were changed by hand. The witness itself is **not generated**.

Public Racket returns bottom-up layer colors `(2,2,5)`; the rival returns `(2,5,5)`. They disagree at row 14, columns 5–7: Racket gives 2 and the rival gives 5. The exact input, complete public Racket output, rival output, differences, validator statuses, and baseline provenance are all retained in [comparison.json](checks/audit/cde6cd1740f9/comparison.json); the unmodified public execution receipt is [witness-racket.json](checks/audit/cde6cd1740f9/witness-racket.json).

**Lesson probe.** Ordinary inputs use seed 73, medium, sample indexes 0–7, with no overrides. The eight demos cover the declared profiles/structures and eliminate the declared rivals. Passing these actual Racket-labelled demos and the handmade witness as query to `lesson_identifiable` returns `[]`, while the new rival survives every demo and fails that query. This is additional evidence of the undeclared rival; externally assembled handmade queries are outside the notes' guaranteed cyclic production assembly.

**Scope and severity.** This is an actionable teaching coverage weakness in the stated general complete-layer/count rule. It is not an incorrect Racket label, an exact-control failure, or evidence that the documented finite declared-rival guarantee is false. The notes expressly limit identifiability to named rivals, and generation deliberately supports four structural templates. The witness is stronger than merely oracle-executable outside-domain data because the task's own strict validator accepts it. No source was edited; no random audit target was rerolled; no other task or private solve data was inspected.

**Suggested repair.** Add a grouped-layer partition choice that emits `(p,p,s)` as well as `(p,s,s)` for `k=3`, retain scattered source rows, and add this count-ignoring rival and its `8+1` witness to the teaching checks. Schedule/count demonstrations so the alternative grouping actually refutes the rival in every promised production/rotation window. Alternatively, explicitly narrow the intended teaching rule to the fixed partitions the generator currently emits, but that would reduce the claimed count-partition generalization.

**Bounded checks and retained files.** Five new recorded commands completed successfully: preparation, three public apply calls, and comparison. The public calls executed 13 grids total in batches of 4, 8, and 1; all outputs were valid and no execution errors occurred. Canonical loading used portable `find_root`, `canonical_path`, and `canonical_pairs`; eight ledger pairs deduplicated to four distinct labelled pairs. No full battery, all-axis census, or universal rival search was performed.

Evidence directory: `WORK/checks/audit/cde6cd1740f9/`. Inputs and public receipts: [canonical-input.json](checks/audit/cde6cd1740f9/canonical-input.json), [canonical-racket.json](checks/audit/cde6cd1740f9/canonical-racket.json), [ordinary-input.json](checks/audit/cde6cd1740f9/ordinary-input.json), [ordinary-racket.json](checks/audit/cde6cd1740f9/ordinary-racket.json), [witness-input.json](checks/audit/cde6cd1740f9/witness-input.json), [witness-racket.json](checks/audit/cde6cd1740f9/witness-racket.json). Source-bound specification and comparison: [probe-spec.json](checks/audit/cde6cd1740f9/probe-spec.json), [reference_rule.json](checks/audit/cde6cd1740f9/reference_rule.json), [comparison.json](checks/audit/cde6cd1740f9/comparison.json); reproducible scripts: [prepare.py](checks/audit/cde6cd1740f9/prepare.py), [compare.py](checks/audit/cde6cd1740f9/compare.py). Invocation/error records: `WORK/checks/commands/audit-cde6cd1740f9-{prepare,canonical-racket,ordinary-racket,witness-racket,compare}.{json,log}`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-40d2bd8fd0adb4ae-v0001/audit_assets.json), manifest SHA-256 `1765451860f3d979c8585ed25ab7187c999f896f70b2040d2afb24fba75186b9`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `66c20ab0c44e2199caf1664e2b994fa55462fe3383efcb6addc2085b8c7fbbff`.

# Decisions for cde6cd1740f9

Assignment `review-754f4d9eaf06696d`; baseline v4.1.0 SHA-256
`2d1797e25875f199afd1e28c88efadb3c974827bce9792e09361120fa6b6ede4`;
final v4.2.0 SHA-256 `66c20ab0c44e2199caf1664e2b994fa55462fe3383efcb6addc2085b8c7fbbff`.

## D1 — Reproduce the unresolved audit against selected bytes

The current `review-40d2bd8fd0adb4ae:v0001` finding identified missing 8+1 support.
The selected baseline was measured, not an unintegrated prior patch. An independent
probe confirmed the count-ignoring rival fits 4/4 unique canonical pairs and
24/24 baseline draws (seed 73, indexes 0–7, three bands), while an authored
reference-valid 8+1 witness refutes it. This is missing teaching support.

The older portability finding concerns a different historical source. It prompted
portable helper use and an actual isolated test run, but is not reported as a new
current-baseline failure. No review-index or approval status was edited. Current
evidence supports maintainer resolution of the count-support finding; no external
historical return was needed as measurement evidence.

Evidence: `checks/counts-before/`, `checks/count-regressions-before.*`,
`checks/task-tests/`.

## D2 — Add ordinary 8+1 cases while retaining 5+4

Previously, a two-color k=3 source always assigned one color to the five-cell
base and the other to middle plus apex. The new structure assigns primary to
base plus middle, secondary to the apex. Both satisfy the unchanged complete-layer
rule. The default second k=2 column preserves mixed-size composition; a one-column
override gives a minimal witness. All four canvases support both structures.

Rejected alternatives: a fixture/override alone leaves ordinary lessons shortcut-
valid; replacing 5+4 with 8+1 creates an opposite fixed-boundary shortcut; arbitrary
nine-cell color partitions can violate the intended domain. The baseline rationale
for excluding 8+1 is unknown beyond the four hand-coded structures.

The five controls retain exact meanings: canvas profile, structure, one/two active
columns, primary palette value, and one of three lawful column layouts. Source
rows remain scattered, with disjoint on-canvas output footprints. Source color
order and column identity are unchanged. The canvas counterexample was rebound
to an actual final-source draw; its prior bytes remain in `checks/retained-before/`.

Evidence: task `counterexamples/count_partition_8_1.json`,
`checks/generated-witness-racket.json`, `checks/counts-after/`, and regression tests.

## D3 — Nine demonstrations and a 20-state schedule

The old 16-state schedule combined four profiles/four structures and eight demos.
The replacement uses `profile[i mod 4]` and `structure[i mod 5]` for `i=0..19`.
Coprime periods enumerate all 4×5 combinations, independently varying geometry
and structure. The production contract is nine consecutive demos then one query.

Every ten-pair window contains two of each structure and at least two of each
profile. Removing any one query retains every structure, including both count-
grouping witnesses; remaining demonstration order is preserved. Required-rotation
checks, all starts at seed 0 and focused multi-seed tests verify the named rivals,
including the existing canvas shortcut.

Keeping eight demos could expose a unique grouping witness to a holdout. Random
independent draws would make coverage probabilistic; prohibiting rotations would
narrow the intended contract. Nine demos deliberately pay for redundant support;
minimality among all possible schedules is not claimed.

Measured production: 300/300 sampled lessons pass. Rotations: 3,000/3,000 pass.
Exhaustive fixed-seed starts: 60/60 lessons and 600/600 rotations. Those windows
overlap (87 unique inputs); the random census has 2,999 unique inputs. Finite
rival checks do not exhaust all seeds or certify arbitrary smaller lessons.

## D4 — Literal scalars and truthful rival namespaces

Baseline defect lint found 51 scalar-coercion warnings. Seeds require literal
integers; sample indexes literal nonnegative integers; exact integer controls
reject booleans, floats and strings. Negative integer seeds remain legal.
Metadata validation compares types and values; documented `None` defaults remain.

The semantic gate rejected four false canonical-fit declarations. Identity,
gravity, monochrome and fixed-k3 remain semantic negatives, but leave
`CANONICAL_SHORTCUTS`. Both retained canonical shortcuts are actually executed
against all unique canonical pairs. Suppressing warnings or weakening the gate
was rejected.

Evidence: before battery 10/12; tests-first 21 failures/nine passes; after battery
12/12 and all 30 regression tests pass. The 12 existing tests retain geometric
and axis assertions while accommodating the new structure and portable helpers.
The isolated stage passes all 52 tests, including ten prototype tests.

## D5 — Preserve canonical authority and propose one semantic parameter

The original-family priority was addressed with runnable `base_edge`, chosen
once per episode. Bottom returns the canonical program byte for byte; top changes
only `(row (- (- h 1) i))` to `(row i)`. Source roles, bottom-up color order,
exact counts and complete-layer construction remain invariant. This is a rule
variant, separate from input-distribution controls.

Changing widths/cell totals would change the core reasoning; modifying selected
canonical execution is unnecessary; Python-only answers would not establish
Racket agreement. One useful parameter suffices without inventing a second.

The prototype verifies canonical source identity, executes both rules via the
included Racket bridge, separates public challenges from private labels, snapshots
participating sources, and refuses mixed evidence in nonempty output directories.
It reads the current demo count. Initial missing-code test failures and a source-
change guard failure during development are retained; final evidence is bound.

Ten final tests pass; canonical replay is 8/8 ledger records (four unique pairs).
Seeds 0 and 1 show both settings, and every one of nine demos refutes the alternate
edge in both episodes. Bottom SHA-256 is
`1eabf7f4ae2d7acbaa8ba9db677c140a76bfabce59d672ea30d1ba06cbd3fae5`;
top is `91d4501cca0e45c24ff312e65c64ae789ce93e1e4bfb99348075641d287a65cc`.

Status **proposed prototype**: no production API, selected-rule or approval change.
Evidence covers two seeds at one band/start and the alternate-edge rival. Top
outputs can occupy former source rows; this is lawful because row positions are
discarded, without changing source color-reading order.

## D6 — Preserve genuine solves and separate findings-only audits

The initial blind lane was completed before rule inspection: one submission,
4/4 visible checks, hidden result unknown. The final-source post-repair lane has
one submission, 9/9 visible, earlier exposure yes, reference consultation during
solve no. Actual code and frozen notes are retained. A passing first attempt is
not padded with invented failures, and query labels were not consulted.

Both assigned audits reproduce separate shortcuts with actual authority outputs;
their generators remain unchanged. Passing existing audit tests cannot close a
new rival outside those declarations. `AUDIT.md` distinguishes canonical fit from
ordinary generated-support sufficiency.

## D7 — Report broader failures without crossing the task boundary

The configured suite ran once: 19 failed, 995 passed, three optional-Torch skips,
18 passing subtests. Targeted reruns and read-only diagnostics classify all 19
immediate causes: 12 PID/liveness, two archival expectations, two raw interpreter
path comparisons, two stale protocol assertions, one socket denial. Twenty-one
relevant files match the original upload. Exact evidence and limits are retained.

The main task's 12-stage battery and 52 isolated tests remain separate passing
measurements. Shared runtime/test/catalog fixes exceed this assignment's scope
and are feedback, not concealed edits. These results do not make the wider suite
green or establish that unverified descendants actually survived.

## D8 — Preserve exact evidence and verify portable application

Large census reports are losslessly compressed with the native manifest schema,
raw/encoded hashes and verified decompression. The after battery's exact schedule
copy remains unchanged; failures and actual solve attempts remain retained.
Fresh-source replay verified all ten changed files using the declared runtime
closure (362 of 85,904 source entries), with Git rooted at the fresh WORK. The
exact source patch hash is `5743c90675397a2ce68435f797ef8c1e0323e9e8ac64a74522c693bd0676e3a8`.
An independently installed venv and Racket then passed all 52 isolated task tests.
The initial assignment-dependent shorthand failure is preserved; the successful
command supplies the known task ID explicitly. See `checks/replay/handoff.json`
and `RESULTS.json`. The final package keeps the same tested source delta. The
supplied builder checks unchanged unrelated sources, identity and evidence budgets.
