# Current account: b8cd4b7fd7a4

## Intended rule

A lawful input is a 5–14 by 5–14 rectangular ARC grid with exactly two equal-colored nonzero markers (colors 1–7). The markers share a row, column, or 45-degree diagonal and have at least one strict interior lattice cell. The output is a same-size zero grid whose strict segment interior is cyan (8); both endpoints are omitted.

The selected canonical Racket authority was not changed. `RULE_HASH = 1b1807245196` remains pinned and the final authority-sync/rule-smoke checks are green.

## Decisions now in force

- Exact public axes are `grid_h`, `grid_w`, `orientation`, and `endpoint_color`; all are pixel-observable and every legal override is constructive.
- Ordinary generation uses an eight-profile schedule. Six profiles are exact public 8x8/9x9 anchors, one is an 8x9 envelope profile, and one ranges independently over every height and width in 5..14.
- Orientation order is horizontal, diagonal, vertical, diagonal, horizontal, diagonal, vertical, diagonal. Every four-pair cyclic lesson window therefore contains diagonal evidence.
- Profiles 0 and 4 retain public color 3; all other profiles draw from 1,2,4,5,6,7. The ordinary stream therefore reaches every legal marker color and refutes the canonical-fitting “only color 3” rule.
- Difficulty changes only segment distance: easy favors short segments, medium spans the legal range, and hard favors long segments. It does not alter the rule or the exact-axis domain.
- `self_check`, `strict_canonical_like`, and `observe_overrides` all use the same strict pixel-derived analyzer. Invalid seeds, indices, overrides, ragged grids, extra points, mixed colors, adjacent endpoints, and nonaligned points are rejected.
- Three demonstrations are required. Declared rivals cover color-3-only, axis-only, endpoint inclusion, and painting with the marker color. Every cyclic start and every query rotation of the eight-profile schedule is checked in the focused tests.

## Reversed prior choices

The selected baseline (`e7649d7db40bde3be4c21538296a6165ea427797570ede36856aa3fa1217bbe7`) advertised `grid_h`/`grid_w` while consuming `height`/`width`, exposed controls that did not describe real pixels, accepted arbitrary negative modes, and had no pinned `RULE_HASH`. A retained prior audit showed requested `grid_h=14, grid_w=5` was ignored in 100/100 paired probes. Those choices are replaced by one exact, lawful manifold with no diagnostic negative modes mixed into training. Evidence: `checks/before/`, `checks/after-v4/`, and `checks/task-tests-final/`.

Version 3.0.0 initially kept lawful semantics but its ordinary stream emitted only six of seven legal colors, only four shapes, and 453/1000 distinct hard-band inputs in the independent probe. Version 3.1.0 broadens the natural stream rather than relying on forced overrides: all seven colors, 73 observed shapes, and 650/1000 distinct hard-band inputs. Evidence: `checks/reference-probe-final.json` versus `checks/reference-probe-final-v3.json`.

## Verification and known limits

Final generator SHA-256: `f03d683edcc460db03902653cee73c2f151420afd960d1d21c053500a5fcd0de`.

- Official battery: 12/12 stages green with strict rotation and schedule-period checks.
- Portable focused tests: 79/79 passed.
- Independent probe: 4,000 ordinary draws, zero determinism/self-check/strict failures; 27/27 independent Racket comparisons matched.
- Lesson census: 300/300 lessons materialized, 0/300 production ambiguities; 1,200/1,200 query rotations checked, 0 ambiguous; 907 exact unique inputs.

These are finite checks against the declared and searched rivals, not a proof that every possible learner hypothesis is excluded. The stream intentionally stays on the exact-two-marker lawful domain; robustness to extra objects, arbitrary slopes, adjacent endpoints, colors 8–9 as markers, or out-of-range canvas sizes is out of scope and rejected rather than labeled. The schedule is periodic by design; downstream samplers should preserve at least three demonstrations and should not expose sample-index metadata to the learner.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-e15551ffde646c62:v0002`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `e7649d7db40bde3be4c21538296a6165ea427797570ede36856aa3fa1217bbe7`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Same exact old source e7649d7d and named ignored grid controls/negative-domain issues as v1; accepted f03d683e repair consumes exact pixel-observed controls and excludes unsupported negative modes. Reports79 tests,4000 bounded stream cases,1200 query rotations retained. No blanket closure of other tasks or universal correctness claim.

### Assessment or prior finding

## b8cd4b7fd7a4

Source SHA256:
`e7649d7db40bde3be4c21538296a6165ea427797570ede36856aa3fa1217bbe7`.

**A2 — reproduced ignored-axis defect.** The advertised `grid_h`/`grid_w` controls
are not the keys consumed by generation (`height`/`width` are used). For seeds
0..99, index 0, difficulty null, `grid_h=14, grid_w=5` produces exactly the same
grid as omitting both overrides in **100/100 paired comparisons**. None of those
requests returns its requested shape. Full grids and dimensions are recorded in
`checks/audits/b8cd4b7fd7a4-controls.jsonl`. Fix key alignment and add
requested-versus-observed shape assertions; do not make the observer simply echo
requested metadata.

**Domain question, not a proved normal-output defect.** Explicit negative modes
are accepted by self-check even when outside the stated aligned-endpoint domain.
At seed 0/index 0, `no_endpoints` is blank but Racket paints an 8 at (0,0);
`non_aligned` produces endpoints (1,1) and (5,6), while Racket paints a sign-step
diagonal at (2,2)..(6,6) rather than a segment between those endpoints. These are
actual recorded outputs, not interpreter crashes. Clarify whether these modes
are diagnostic-only; do not mix their arbitrary rule extensions into ordinary
training data without an explicit semantic contract. The adjacent-endpoint case
returns blank, which is consistent with having no strictly interior cells and
is not itself reported as a defect.

**Checks that did pass.** The sampled ordinary seed-0 diagonal case executes as
expected; all three canonical pairs (two train, one test) exactly match Racket.
No canonical-authority defect was reproduced. Scope checked: 100 paired control
requests, four ordinary/negative probes, three canonical pairs. No patch was made.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-e15551ffde646c62-v0002/audit_assets.json), manifest SHA-256 `424aad8e42f969b255d22f5b00ea68570c024acd5fb39a2d32c7d7e791b6e294`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `f03d683edcc460db03902653cee73c2f151420afd960d1d21c053500a5fcd0de`.

# Design and review decisions for b8cd4b7fd7a4

Final generator SHA-256: `f03d683edcc460db03902653cee73c2f151420afd960d1d21c053500a5fcd0de`.

## D1 — Keep the selected Racket authority unchanged

**Choice.** Pin `RULE_HASH = 1b1807245196` and change only the generator/teaching contract.

**Rationale.** All three canonical pairs already matched the selected rule, and the before rule-smoke stage passed. The defects were metadata, domain, controls, and distribution defects rather than a reference-law defect.

**Alternative rejected.** Rewriting the Racket rule to special-case malformed negative modes. That would legitimize out-of-domain labels and add authority churn without improving the lawful task.

**Probe/evidence.** Final `rule_smoke`, `racket_lint`, and `authority_sync` are green in `checks/after-v4/`; 27/27 independent Racket comparisons match in `checks/reference-probe-final-v3.json`.

**Failure mode/limit.** The selected rule’s behavior outside the exact-two aligned-marker domain remains irrelevant because such inputs are now rejected, not labeled.

## D2 — Replace mixed diagnostic modes with one strict lawful manifold

**Choice.** Accept exactly two equal markers, legal colors 1..7, horizontal/vertical/45-degree alignment, and distance at least two. Reject blank, one-point, adjacent, nonaligned, mixed-color, extra-point, bad-color, bool, and ragged inputs.

**Rationale.** The baseline’s `no_endpoints` and `non_aligned` modes had arbitrary Racket extensions and were accepted by a permissive self-check. Mixing them into training would teach behavior not supported by the task description.

**Alternative rejected.** Preserve negative modes behind a `texture` axis. That keeps an exact control whose values do not belong to one coherent semantic domain and complicates lesson identifiability.

**Probe/evidence.** Focused malformed-near-miss tests in `repo/generators/b8cd4b7fd7a4/tests/test_generator.py`; 79/79 portable tests pass in `checks/task-tests-final/`.

**Failure mode/limit.** The generator no longer supplies robustness examples with distractors or arbitrary slopes. That is intentional scope restriction, not general ARC-segment coverage.

## D3 — Make the four public controls exact, observable, and exhaustive

**Choice.** Expose only `grid_h`, `grid_w`, `orientation`, and `endpoint_color`. Use strict keyed draws when overridden and recover all four from returned pixels.

**Rationale.** The prior source advertised `grid_h`/`grid_w` but consumed `height`/`width`; a retained audit reproduced ignored requests in 100/100 pairs. Controls should describe generated pixels, not requested metadata.

**Alternative rejected.** Add aliases for the old keys. Silent aliases preserve ambiguity and make unknown-key rejection weaker.

**Probe/evidence.** Boundary matrix covers 4 difficulties × 4 shape/orientation cases × 3 colors; invalid/unknown controls and invalid seed/index scalars are rejected. Official override stage is green in `checks/after-v4/`.

**Failure mode/limit.** Joint controls are legal because every 5..14 canvas can fit each orientation with distance two. Future axes must be added to both the strict validator and pixel observer.

## D4 — Use an eight-profile curriculum with canonical anchors and one broad profile

**Choice.** Schedule shapes `(8,8), (9,9), (8,8), (9,9), (8,8), (9,9), (8,9)`, then one independently sampled 5..14 by 5..14 broad profile.

**Rationale.** Six exact public profiles maintain strong canonical support; the envelope profile adds nearby variation; the broad profile prevents the learner from equating the rule with 8x8/9x9 canvases.

**Alternative rejected.** Uniformly sample all 5..14 shapes on every draw. That maximizes scale diversity but weakens the explicit profile floor and makes small generated lessons less likely to resemble the public task.

**Probe/evidence.** Official profile-floor stage is green. The final 4,000-draw probe observes 73 shape pairs per band and zero strict/self-check failures (`checks/reference-probe-final-v3.json`).

**Failure mode/limit.** The schedule is periodic. The model does not receive sample-index metadata; if a downstream system leaks it, the period could become a shortcut.

## D5 — Force diagonal evidence into every four-pair lesson window

**Choice.** Orientation schedule: H, D, V, D, H, D, V, D.

**Rationale.** The canonical examples include axis-aligned and diagonal behavior, but an axis-only rival remains plausible whenever demonstrations omit diagonals. Every cyclic four-pair window contains two diagonal examples and at least one horizontal or vertical example.

**Alternative rejected.** Independent random orientation. Randomness gives good aggregate frequencies but allows unlucky three-demo lessons that leave `axis_only` compatible.

**Probe/evidence.** Focused tests enumerate starts 0..15 in all three bands and hold out each of four positions as query; all four declared rivals are refuted by the remaining demos. The official battery was run with `--require-rotations-identifiable --enumerate-schedule-period` and is 12/12 green.

**Failure mode/limit.** These checks cover declared rivals and the finite eight-profile period, not all conceivable rules.

## D6 — Keep color 3 as an anchor while naturally covering all legal colors

**Choice.** Profiles 0 and 4 use color 3; the other profiles draw from 1,2,4,5,6,7.

**Rationale.** All public examples use color 3, so color 3 should remain common. However, `color_three_only` fits all canonical pairs; ordinary lessons need non-3 counterexamples, and the natural stream should reach every advertised color without forced overrides.

**Alternative rejected.** Draw non-anchor profiles from 2..7. Version 3.0.0 did this and omitted color 1 naturally despite accepting it as an override.

**Probe/evidence.** Intermediate probe `checks/reference-probe-final.json` shows the omission; final probe `checks/reference-probe-final-v3.json` shows colors 1..7 in every band. Every cyclic four-pair lesson window has non-3 evidence.

**Failure mode/limit.** Colors 8 and 9 are intentionally excluded as endpoints because 8 is the output paint color and neither appears as a marker in the canonical rule domain chosen here.

## D7 — Let difficulty alter distance, not semantics

**Choice.** Easy samples short legal distances, medium the full legal range, hard the upper half.

**Rationale.** Distance changes perceptual/algorithmic difficulty while preserving the same rule, shape controls, and palette contract.

**Alternative rejected.** Difficulty-specific orientation or color subsets, which could make band identity a semantic shortcut.

**Probe/evidence.** All exact overrides are constructive in every band; independent probe has zero errors across 1,000 draws for each of None/easy/medium/hard.

**Failure mode/limit.** Hard has fewer exact unique inputs (650/1000) than easy (791/1000) because long segments reduce geometry choices on anchor profiles; it remains materially broader than version 3.0.0’s 453/1000.

## D8 — Require three demonstrations and declare concrete rivals

**Choice.** `EXAMPLES_NEEDED = 3`; declare `color_three_only`, `axis_only`, `include_endpoints`, and `paint_endpoint_color` in semantic/lesson contracts.

**Rationale.** These are simple, reference-lawful or visually plausible alternatives that a small model can learn. Explicit executable rivals turn curriculum claims into tests.

**Alternative rejected.** Rely only on witness frequencies or two informal inference guesses. Aggregate presence does not guarantee each complete lesson refutes a rival.

**Probe/evidence.** Lesson census materialized 300/300 lessons (three demos + one query), found 0 production ambiguities in 300, and 0 ambiguous rotations in 1,200 held-out-query rotations; 907 exact unique inputs. See `checks/lesson-census-final.json` and companion summary.

**Failure mode/limit.** The census and generic searched rivals are finite diagnostics, not a proof of unique induction.

## D9 — Build a task-local independent probe rather than duplicate the authority

**Choice.** Add `workspace/reference_probe.py` with independent pixel analysis, oracle, declared-rival mirrors, optional public Racket calls, and a deterministic 1,000-sample-per-band census.

**Rationale.** It gives future agents a cheap, reusable way to detect control/domain regressions and compare Python assumptions against actual Racket receipts.

**Alternative rejected.** Embed canonical answers or private runner internals in tests. That would weaken portability and risk answer leakage into solve lanes.

**Probe/evidence.** Portable task tests import the tool via `reviewer_support` roots; real Racket checks skip only when runtime is unavailable. Final run checked 27 grids against Racket with zero mismatches.

**Failure mode/limit.** The Python oracle is independent code but still human-authored; only the Racket receipt binds it to selected authority.
