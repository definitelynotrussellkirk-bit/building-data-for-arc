# Current decisions: 2b34f380ed25

## Canonical behavior and authority

Original family: training:4e7e0eb9. Version 3.1.0 retains the canonical Racket
authority `76c7916140ea` unchanged. Exact maximal runs of three nonzero cells
identify macro bands; full uniform nonzero/non-yellow gap lines split panels.
Yellow gap strips exchange equally sized macro halves in positional order.
This is distinguishable from geometric reflection once each half contains two
or more macro bands. Unbalanced marks preserve the marked panel and suppress
the unmarked fill branch. An unmarked panel fills its 1-valued macro cells only
when it has exactly one distinct nonzero/non-1 macro color. Gaps and margins
remain unchanged. The Python `_extract_facts` and `rule_mirror` implementations
are unchanged from version 3.0.0.

## Sampling and teaching decisions

The prior independent profile mixture sometimes supplied three demonstrations
compatible with geometric reflection, then a four-band half-swap query. The
source-bound seed-0/index-8 lesson in `counterexamples/reflection_lesson.json`
records this ambiguity. Canonical examples cannot eliminate that rival: their
marked panels have only one band per side.

The current default sampler cycles through three semantic lanes: a strengthened
`four_panel_mixed` scene with both four-band counterexamples, an unbalanced
mark guard counterexample, and one randomized original context. The four-panel
scene has a 6x6 macro board: top-left 2x2 fill, top-right 2x4 vertical half-swap,
bottom-left 4x2 horizontal half-swap, and bottom-right 4x4 preservation. Both
axis-specific reflection rivals must differ before this scene is returned.
The context lane retains all six exact public anchors and all ten original
general profiles. All sixteen original scene-profile overrides remain visible.
Geometry, colors, and context choices vary within lanes; the period is three
for the lane sequence, not for the complete grid or context profile.

An intermediate repair introduced a seventeenth `wide_swap_mixed` profile.
Its lessons passed the finite rival census, but the generic linter only
qualifies sixteen finite-enum values. The final repair consolidates that new
case into the existing four-panel family instead of omitting a supported
override from metadata. The family's four action roles are unchanged; its
marked panels grow from two to four bands. `row_split_mixed` keeps its original
vertical-swap-plus-fill construction. Intermediate source and checks are
retained in the return; final evidence is bound to the consolidated source.

Five demonstrations and one query give two instances of each lane in every six
consecutive requested indices. Holding out any one leaves both kinds of
counterexample in the demonstrations. The production worker can reject or
deduplicate inputs; accepted-index coverage and finite identifiability claims
therefore come from the source-bound lesson census, not from the period alone.
Four explicit canonical-fitting rivals cover full reflection, either reflected
axis alone, and ignoring an unbalanced mark. This finite rival family does not
exhaust all possible alternative rules.

Previously, unbalanced profiles sampled unrestricted macro colors in the
marked panel. Only 1/3200 inspected forced-profile draws made ignoring that
mark visibly wrong. The marked panel now contains at least one 1 and exactly
one non-1 color, so its preservation depends on the mark. The separate
unmarked companion panel still fills. The retained pre-repair witness is
`counterexamples/unbalanced_guard.json`.

## Controls and tests

Seed and sample index must be exact Python integers; Boolean, float, string,
and missing values are rejected. Sample indices must be nonnegative; signed
integer seeds remain supported. Explicit `scene_profile` overrides remain
observable and bypass the default lesson schedule. No exact height/width
controls are advertised.

The inherited test in `tests/` now uses public `reviewer_support` helpers to
find canonical data and selected source in both repository and copied runtime
layouts. Its nine test methods and all 49 assertion calls were preserved. The
old audit `review-d3e2428dfb7dde6a:v0001` is a lead for this portability repair;
its index disposition was not changed automatically. Maintainer triage should
use this return's relocated test evidence to assess that finding explicitly.

## Proposed parametric extension

`workspace/parametric/prototype.py` exposes one episode-level `mark_action`:
`half_swap` (exact canonical default) or `reflection` (reverse partner order).
It preserves macro decoding, panel roles, mark balance, fill, and repainting.
All retained labels and parameter-rival predictions execute the instantiated
Racket program. See its README for commands and public/private boundaries.
This is a proposed research prototype, separate from canonical approval or
training admission.

## Remaining limits

General scenes keep solid nonzero 3x3 macro cells, zero gaps, one mark per panel,
and the declared panel layouts. General macro colors exclude 4 and the current
separator color; their canonical occurrences remain supported by exact public
anchors. Arbitrary intersecting marks, broader palette roles and arbitrary
layout support were not added. The four-panel witness has meaningful 27x27 content;
the prototype also checks 30x30 queries with more active macro cells. No
corpus-wide size-mixture or universal identifiability claim is made.

## Current owner source and evidence limits

Accepted the five-demo curriculum repair, strict scalar guards and portable inherited tests. The canonical Racket rule is unchanged. The reviewer reports 12 green battery stages, 27 tests plus 678 subtests in copied and fresh dependency runtimes, and 300 lessons with 1,800 clean query rotations. The fresh replay extracted 340 of 98,234 files and used host NumPy/Pillow. Earlier lint, padding, readiness and packaging failures remain retained. The half_swap/reflection prototype has three reported episodes and 61 Racket applications. Separately, the owner replaced setting-order public filenames with hashes of visible challenge contents, passed 13 focused tests and regenerated two episodes. The original source and reports remain separate. General macro-block support is bounded; variants, production parameters and training data are unapproved.
## Current reviewer considerations

Source SHA-256: `d9ac2d87d645930fe23fef098dd36f1f9487cee15f5d83e412864694d6e66864`.

# Decisions: 2b34f380ed25 canonical repair and proposed extension

## Scope and source identities

Assignment `review-eb54c6c656f46915` remains unchanged; original family `training:4e7e0eb9`. The baseline selected generator is VERSION `3.0.0`, SHA-256 `b04d2f58c34c7c47940fcd87c8cfedc9024f759347c88c091b92dd57d9ccac1f`. The final repaired generator is VERSION `3.1.0`, SHA-256 `d9ac2d87d645930fe23fef098dd36f1f9487cee15f5d83e412864694d6e66864`. Intermediate repair SHA-256 `e2172d92fb1ce37549d8c56d1cb8c1fedba7ebc24b4507193eb7d12de9520b7d` is retained with its own successful census and its subsequent finite-enum lint warning.

**No canonical Racket authority was changed.** Selected rule hash remains `76c7916140ea`; normalized callable source SHA-256 is `c0925c9283442740e750843657745ed338edfa2e28f2356df04428215feaea48`. The Python macro decoder and selected transformation remain unchanged. The repair changes sampling, explicit teaching contracts, argument validation and test portability. Proposed rule variants remain separate research artifacts.

## D1: Teach order-preserving half exchange explicitly

The yellow mark exchanges equal-size halves in positional order. It does not geometrically reverse the bands. Every labeled canonical pair is compatible with reflection because the marked panels have one band per side. The baseline's seed-0/index-8 three-demo lesson followed by index-11 query leaves this rival alive; the query differs by 216 pixels. Evidence: `checks/diagnosis/reflection_probe.json`, `input.json`, `expected.json`, `reflection.json`, and executed selected-reference receipt `racket.json` in the same directory. `QUESTION_ANSWER.md` gives the exact input and command.

The final repair strengthens the existing `four_panel_mixed` profile from a 4×4 to a 6×6 macro board. Its panel sizes and actions are 2×2 fill, 2×4 central vertical half exchange, 4×2 central horizontal half exchange, and 4×4 multicolor preservation. Both marked panels are asymmetric enough to distinguish half-swap from geometric reflection. One scene therefore refutes full reflection and either axis-only rival. The input has meaningful 27×27 content and retains the existing panel, band, symbol, fill/preserve and painting semantics.

Rejected alternatives were changing the Racket rule to match the colloquial word “mirror,” trusting the existing random four-band profile frequency, or adding only a vertical witness. The first changes the authority, the second leaves short lessons ambiguous, and the third leaves horizontal-only reflection untested. Existing exact public anchors and all ten prior general profile names remain available in the context lane and as explicit overrides. Explicit `row_split_mixed` retains its original 4×2 vertical-swap-plus-fill branch; `four_panel_mixed` is expanded while preserving all four action roles.

## D1a: Consolidate the witness into an existing public profile

Intermediate source `e2172d92fb1ce37549d8c56d1cb8c1fedba7ebc24b4507193eb7d12de9520b7d` added `wide_swap_mixed` as a seventeenth public scene-profile value. The after-battery linter reported `finite_enum_too_large`: 17 alternatives exceed its 16-value probe cap, leaving a sampled override domain. Evidence: `checks/after/checks/2b34f380ed25_after_lint.log`. Other successful intermediate stages do not erase that warning.

Rather than conceal an alias or drop an old valid override name, the final source strengthens `four_panel_mixed`, whose original `[fill, vertical, horizontal, preserve]` action signature already contains both required marked operations. Increasing its macro extent supplies two bands per side without changing those roles. This is simpler than an internal wide branch under `row_split_mixed`, which would broaden the latter from vertical-plus-fill to a second topology. All 16 original public names remain; no seventeenth override is advertised or accepted.

The final-plan regression was written and run before implementation. `checks/diagnosis/consolidation-before-command.json` records the exact direct Python command, environment, source hash and exit `1`; `consolidation-before.log` reports 43 failures, 6 passes and 620 passed subtests against intermediate source. The failures reflect the 17-name/new-profile implementation against the intended consolidated contract. Final green and gate outcomes are recorded below, separately from this retained red run.

## D2: Make unbalanced-mark preservation depend on the mark

The baseline unbalanced profiles usually used multiple non-1 colors in the marked panel, so removing the mark still preserved it under the ordinary fill rule. Only 1/3,200 inspected forced-profile draws distinguished “ignore unbalanced marks.” The finite census and exact old-source witness are in `checks/diagnosis/unbalanced_probe.json`, `unbalanced_input.json`, `unbalanced_expected.json`, `unbalanced_rival.json`, and `unbalanced_racket.json`.

Both marked and companion panels now contain at least one 1 and exactly one non-1 color. The unbalanced marked panel preserves its 1s; its separate unmarked companion fills. This makes the cue's effect observable without adding a transformation. Merely asserting that the marked panel is unchanged was rejected as insufficient: unchanged pixels alone do not show which condition caused preservation.

## D3: Schedule complete lessons, including query rotations

The ordinary sampler repeats three **semantic lanes**: `ordered_halves`, `unbalanced_guard`, and `context`. Colors, contexts and applicable dimensions vary; this is not a three-grid replay. The context lane retains all six exact public anchors and all ten original general profiles. Every `scene_profile` remains explicitly overrideable, and observed profiles must match the returned grids.

The export/teaching contract is **five demonstrations and one query**, with the remaining demonstration order preserved when a different pair becomes the query. Six consecutive requested indices contain two instances of each lane. Any held-out pair leaves an ordered-halves witness and an unbalanced-guard witness among the demonstrations. Four or fewer demonstrations do not give that same redundancy for all query positions under this three-lane design. A fully independent profile mixture or a fixed privileged query position was therefore rejected.

The declarations name four unique rivals: `geometric_reflection`, `vertical_reflection`, `horizontal_reflection`, and `ignore_unbalanced_marks`. They appear in three registries, which are twelve bindings, not twelve distinct hypotheses. All fit all six usable canonical labels. Witness predicates require actual output disagreement. This finite rival set is useful evidence, not a complete description of every possible shortcut.

The worker may reject or deduplicate inputs, advancing accepted indices. Consequently the arithmetic lane argument is about requested indices; actual exported lesson claims require accepted-index materialization evidence. The full fixed-seed report retains those indices rather than inferring them from the period.

## D4: Reject invalid controls and repair source portability

Seed and sample index now require exact Python integers, excluding booleans, floats, strings and missing values. Sample indices must be nonnegative. Signed integer seeds remain supported. Silent coercion was rejected because it hides invalid calls and can desynchronize the schedule from the randomness key. Unknown overrides and unsupported difficulties still reject explicitly.

The inherited task tests previously used a private import and fixed ancestor-depth canonical-data path. They now use public `reviewer_support.find_root`, `load_selected_generator`, `canonical_path`, and `canonical_pairs`. Their nine methods and 49 assertion calls were preserved. The source-portability repair and every actual attempted command are recorded in `checks/diagnosis/portable-tests-repair-evidence.json`. It distinguishes inherited-test successes from intermediate failures of the newly introduced, not-yet-implemented contracts and from Racket startup timeouts.

The new behavioral contract tests preceded implementation: guarded baseline pytest was red in `checks/diagnosis/review_contract_before_pytest.log`. The intermediate focused run passed **7 methods and 679 subtests** in `checks/diagnosis/review-contract-after-direct.log`, before the final profile consolidation. These Python checks complement selected-Racket census evidence. They are not a substitute for final source-bound portable verification. The old retained portability audit was not automatically marked resolved; its maintainer disposition remains explicit.

## D5: Bounded verification and status at this revision

For intermediate source `e2172d92fb1ce37549d8c56d1cb8c1fedba7ebc24b4507193eb7d12de9520b7d`, the retained selected-Racket census `checks/schedule-census.json` and companion `checks/schedule-census.summary.json` enumerate seed `0`, starts `0..2`, and easy/medium/hard. Results: **9/9 lessons materialized; 54 pairs; 54/54 required query rotations checked; 18 unique inputs; zero ambiguity, hook-warning, scoring-error or materialization-error counts.** Production and rotation verdicts are both `no_ambiguity_found`.

This is complete start-residue coverage at that fixed seed, not exhaustive support over all seeds. Overlapping lessons account for the difference between 54 pairs and 18 unique inputs. The report records four unique declared rivals and their six-of-six canonical fits.

The completed larger selected-Racket census is summarized in `checks/lesson-census.summary.json`, bound to the same generator source and rule. Its execution exited `0`: **300/300 requested lessons materialized, 100 in each of easy/medium/hard; 1,800 pairs; 1,800 required query rotations; 1,592 unique inputs.** All production and rotation ambiguity, hook-warning, scoring-error and materialization-error counts are zero. Both verdicts are `no_ambiguity_found`. Requested start indices are `INDEX=0..99` per band; seeds follow the recorded recipe `sha256('lesson-census:v1:TASK:BAND:INDEX')[:8] as uint32`, with `TASK=2b34f380ed25`. Each bundle has five demonstrations and one query. Every labeled pair is held out once while preserving the other pairs' order. This is the sampler's six-position rotation period; the generator's semantic lane period remains three.

The 1,800 pair count is not a unique-input count, and these sampled lessons do not exhaust every seed, accepted-index schedule or undeclared rival. The compact summary binds the full original report by path, bytes and SHA-256. `checks/lesson-census.compression.json` retains the exact original `lesson-census.json` mapping (34,795,502 bytes, SHA-256 `384570e891c774b4fa12297d76a5fd84c7dd9e37a866eb5ff21ef0746eaa6882`) to `checks/lesson-census.json.gz` and gives restoration instructions.

The preceding results belong to intermediate source `e2172d92fb1ce37549d8c56d1cb8c1fedba7ebc24b4507193eb7d12de9520b7d`. Final-source evidence is separately bound to `d9ac2d87d645930fe23fef098dd36f1f9487cee15f5d83e412864694d6e66864`:

| Final verification | Observed result | Evidence |
|---|---|---|
| Focused consolidation regression | 7 methods and 678 subtests passed | `checks/consolidation-after.json`, `checks/consolidation-after.log` |
| Required-rotation after battery | 12/12 green; zero advisory, failed, interrupted or pending stages | `checks/after-final/result.json`, `checks/after-final/checks/2b34f380ed25_after_battery_summary.json` |
| Portable aggregate task tests | 27 ordinary tests plus 678 subtests = 705 JUnit cases; all pass; zero failures, errors or skips | `checks/task-tests/result.json`, `checks/task-tests/checks/task_tests.xml` |
| Fixed-seed complete lane starts | 9/9 lessons, 54 pairs, 54 query rotations, 18 unique inputs; no ambiguity or errors/warnings | `checks/schedule-census-final.json`, `checks/schedule-census-final.summary.json` |
| Larger finite lesson census | 300/300 lessons, 1,800 pairs, 1,800 query rotations, 1,592 unique inputs; no ambiguity or errors/warnings | `checks/lesson-census-final.summary.json`, `checks/lesson-census-final.compression.json`, `checks/lesson-census-final.json.gz` |

Both final census executions exited `0`; production and required-rotation verdicts are `no_ambiguity_found`. Fixed-seed coverage remains seed `0`, requested starts `0..2`, across the three bands. The larger census uses `INDEX=0..99` per band and the same exact SHA-256 seed recipe above. All materialization, scoring, hook-warning and ambiguity counts are zero, including rotation-specific counts. Final full-report compression maps exactly 41,560,334 uncompressed bytes, SHA-256 `3288949c45a4153851eb61cafe58053dc52fbbfdbee82ccbdcafacf840a2604d`, through the retained native gzip artifact; no report bytes were changed by compression. These are finite declared-rival checks, with repeated/overlapping pairs counted separately from unique inputs.

**Fresh relocated replay and focused verification passed.** The supported dependency-closure replay extracted 340 of the original packet's 98,234 files, applied source patch SHA-256 `85f67240dc7c3b1f3850428975cf69d2ea0f8702cd8db517e3ba010a685b1593`, and verified all ten changed files. The separately created environment and its own pinned Racket runtime passed the same 705 JUnit cases (27 ordinary tests plus 678 subtests), with zero failures, errors or skips. This was a declared-runtime dependency-closure replay, not a full-packet extraction. Exact commands, extraction inventory, environment scope and completed test receipts are in `checks/replay/`, summarized by `checks/replay/final-summary.json`. `checks/final-source-binding.json` confirms no source changes after replay. Finalizing the return reports and evidence did not alter the tested patch.

## D6: Proposed parametric rule prototype, separate from the repair

A suitable small parameter is `mark_action ∈ {half_swap, reflection}`, selected once per episode. `half_swap` is the exact canonical/default source. `reflection` reverses partner order by changing only the two Racket `zip-lists` pairing expressions. Macro decoding, panel splitting, mark balance, unmarked fill, repainting, and original-macro overwrite semantics remain invariant. This is **proposed prototype** status, not a production parametric API or approved new authority.

The runnable source and instructions are `repo/generators/2b34f380ed25/workspace/parametric/prototype.py` and `README.md`; focused tests are `repo/generators/2b34f380ed25/tests/test_parametric_mark_action.py`. Exact commands, exits, source hashes and aggregate results are in `checks/parametric/command-1-v2.json`, `command-2-v2.json`, `tests-v3.json`, and `final-summary-v2.json`.

The retained seed-17 two-setting run is `checks/parametric/episodes-s17-v2/manifest.json`; seed-18 automatic selection is `checks/parametric/episode-auto-s18-v2/manifest.json`. These record three complete episodes, 15 input/output pairs, and 11/11 focused prototype tests. Each episode has three demonstrations and two 30×30 queries; both first demonstrations and both queries distinguish its setting from the other declared setting. Default canonical parity is checked on all six original pairs. Public challenge files omit the parameter, program and query outputs; controller/private records retain them.

Exact instantiated Racket raw-source hashes for seed 17 are `de12b6e4b34e308f1c274e7b07e8de63ed309376b464f63059275d4573a0775d` for `half_swap` and `906260926f702956fee5df8dcaa491b1cb11fb48e49a590e1b7de77817ba4bc0` for `reflection`. The programs are materialized as `private/episode-0.rkt` and `private/episode-1.rkt` in that episode directory. Labels and parameter-rival predictions were executed with Racket; no Python-only prototype labeling is claimed.

An earlier prototype's zero padding truncated uniform divider rows, collapsing the intended query distinction. The repair extends those dividers through padding and asserts that both queries distinguish the setting. Failure evidence is retained in `checks/parametric/v1-query-observation.json`, `query-regression-red-v1.json`, `authoring-iterations-v1.json`, and `failure-source-v1/`. This remains bounded two-setting, seeds-17/18 evidence. Two-band ambiguity is recorded honestly rather than called a distinguishing witness.

## D7: Solve records preserve their exposure and evidence limits

The final-source exposed solve finished with one ordinary revision and **5/5 visible demonstration matches**. Earlier reference exposure is declared **yes**; reference consultation during that solve phase is declared **no**. Hidden query correctness remains **unknown**. Evidence: `solve/summary.json` and `solve/FINISHED_NOTES.md`. This is an exposed authoring solve, not a blind benchmark or an intentional teaching negative.

The earlier separate blind solve retained one ordinary revision and **4/4 visible demonstration matches**; hidden query correctness is also **unknown**. Evidence: `solve-blind/summary.json`. The two records are distinct tasks/phases and are not combined into a single success rate. Neither record establishes training admission or unseen-query correctness.

## Self-review and remaining restrictions

The new schedule adds a visible curriculum regularity, but the contract is evaluated from demonstration input/output pairs against actual competing transformations, including axis-specific rivals; the fixed-seed selected-reference census also checks arbitrary held-out query positions. This does not rule out a solver exploiting sample metadata or an undeclared alternative, and public challenges must not expose controller metadata.

General scenes still use solid nonzero 3×3 macro cells, zero gaps and the declared panel layouts, with at most one mark per panel. General macro palettes exclude 4 and the current separator color; their canonical uses are supported by exact public anchors. Arbitrary intersecting marks, nonuniform macro textures and broader palette-role support were not added. Prototype 30×30 canvases include zero padding, so size alone is not claimed as additional reasoning complexity. No universal identifiability, approval or training-admission claim follows from this return.

## D8: Additive promotion adapter and source-bound qualification

Assignment `review-ed6cd7fc372219b1` did not alter the approved generator or
canonical authority.  The selected generator remains VERSION `3.1.0`, SHA-256
`d9ac2d87d645930fe23fef098dd36f1f9487cee15f5d83e412864694d6e66864`,
and rule hash `76c7916140ea`.  The retained research prototype already modeled
the finite `mark_action` choice between exact canonical `half_swap` and the
geometric `reflection` rival; this review added only the repository promotion
boundary around that prototype.

`workspace/parametric/adapter.py` and `promotion.json` now expose exact program
selection plus independent demo/query counts: 3..8 demonstrations and 1..8
queries.  For each seed the implementation builds one deterministic maximum
pool of eight demonstrations and eight queries, then takes prefixes.  Increasing
one count therefore cannot change earlier examples or the other split.  Both
settings receive byte-identical inputs and differ only in Racket program text
and labels.  The original fixed three-demo/two-query API and CLI remain
unchanged.

The contract tests were written before the adapter: their first run failed with
one failure and five errors because `adapter.py` did not exist.  The focused
GREEN run passed 6 tests, the complete parametric group passed 19 tests, and the
selected staged task run passed 35 tests plus 678 subtests.  Tests cover exact
canonical default text, adjacent-source loading, deterministic/count-independent
prefixes, distinct inputs, matched setting inputs, finite identifiability,
live-Racket label parity, and strict rejection of malformed settings/counts.

Protected qualification independently executed both settings at seeds 0 and 17
with 3 demonstrations plus 4 queries, then at seeds 23 and 41 with the maximum
8 plus 8.  All eight jobs were qualified, each demonstration set left exactly
its selected finite setting, and all hidden labels were recomputed through the
protected Racket backend: 40 plus 96 = 136 evaluations.  The final 19-file
source/evidence inventory is `workspace/parametric/evidence/manifest.json`,
SHA-256 `9fa7a9583e946b6c9a49332ddda15239b7d80a5ca412f45e1fc86e248fe57742`.
Its adapter, prototype and contract hashes are respectively
`ba49af2ea163b58d75a7531da20950ee30208cf6db81f1c41a32862cc7c3a0f7`,
`b9dd9c05c663b25ee4c74b9edb5f202e1d4eda03af58c1f0ec2bbbf37d849d23`,
and `651df13588ba4783d8b3c86546eedf3a4df5df7eb644f8cd6a50f27a24c2711d`.

This is qualification, not owner acceptance.  `variant_approved` and
`training_admitted` remain false; no production parametric API or dataset weight
changed.  The next useful action, only if the owner wants this family, is an
explicit acceptance decision bound to the manifest above rather than another
prototype rewrite.
