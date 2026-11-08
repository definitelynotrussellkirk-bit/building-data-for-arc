# Working notes: `5fdbbb5a53ef`

Final reviewed generator: version `3.1.0`, SHA-256 `629d9f4e8580208d8f6d4f70a7ddaf2dcf5f648265e57d8cdd1d3b64946f87da`, canonical `RULE_HASH=b12aeca2f818`.

## Intended rule

Color-9 5×5 frames form a top gallery and a left gallery. Each nonempty 3×3 interior contains one colored shape. For each left/top pair, output 8 for equal rotation class and equal color, 6 for shape only, 3 for color only, and 0 for neither.

## Reversed decision

The baseline deliberately placed joint, color-only, and shape-only anchors in fixed gallery slots to avoid empty relation matrices. That made 64 unique easy 2×2 inputs produce the same `[[8,3],[6,0]]` output (`checks/root-cause/baseline-shortcut.json`). The final generator keeps the semantic anchors but independently shuffles both galleries; the regression is `tests/test_generator.py::test_easy_2x2_relations_are_not_a_fixed_position_template` and the retained summary is `counterexamples/review-546954cb460028f7-v0001/fixed_position_shortcut.json`.

## Current choices

Only exact observable layout axes are advertised: `top_count`, `left_count`, `row_offset`, and `col_offset`; `{top_count:4,col_offset:2}` is explicitly incompatible. Every generated scene contains 8/6/3 teaching support. A seed-hashed approximately 25% canonical-support profile supplies canonical morphology and palette roles without a short sample-index cycle. Structural `self_check` accepts all canonical inputs. The historical fixed-position rule is executable as a declared lesson rival.

## Evidence and limits

Task tests pass 45/45 and the 12-stage after battery is all green. The final census covers 300 production lessons and 1,200 query rotations with 1,200 unique inputs and no ambiguity against declared/simple rivals. This is finite evidence, not proof against every possible shortcut. Racket authority was not changed. No repair finding remains open.
## Current reviewer considerations

Source SHA-256: `629d9f4e8580208d8f6d4f70a7ddaf2dcf5f648265e57d8cdd1d3b64946f87da`.

# Decisions for `5fdbbb5a53ef`

All task-local decisions below apply to final generator SHA `629d9f4e8580208d8f6d4f70a7ddaf2dcf5f648265e57d8cdd1d3b64946f87da`.

## D1 — Keep semantic anchors, remove positional anchors

**Prior choice.** The baseline constructed a joint match, shape-only match, and color-only match in fixed list positions. The rationale was sensible—avoid nearly all-zero matrices—but the position was accidentally predictive.

**New choice.** Construct the same minimum semantic support, then independently shuffle the top and left galleries using named deterministic RNG streams.

**Evidence.** R1 reproduces 64 distinct easy 2×2 inputs with one baseline output. The final semantic witness differs from the fixed-position rival in 579/600 samples, and the final 300-lesson census finds no ambiguity against the declared rival.

**Rejected alternative.** Sampling all frames independently would remove the template but frequently yield sparse/all-zero relation matrices, weakening instruction about 8, 6, and 3. Merely shuffling one gallery would leave a residual positional correlation.

**Limitation.** The anchors still guarantee positive relation types rather than matching a natural unconstrained distribution; this is intentional curriculum shaping.

## D2 — Require every generated input to teach 8, 6, and 3

**Choice.** Each scene includes a shared base shape/color, a shape-only counterpart, and a color-only counterpart. Extra panels are randomized.

**Reason.** A typed-relation task should not be dominated by 0 labels or permit an “everything differs” explanation.

**Probe.** `test_generated_inputs_teach_shape_color_and_joint_matches` checks all bands, while live semantic checks score 600 samples.

**Failure mode considered.** Fixed semantic roles could themselves become a shortcut; D1 randomizes their positions and the explicit rival tests for that exact failure.

## D3 — Advertise only exact, observable input axes

**Choice.** Expose four layout axes: `top_count` 2–4, `left_count` 2–3, `row_offset` 0–2, and `col_offset` 0–2. `observe_overrides` recovers each value from output pixels. Declare `{top_count: 4, col_offset: 2}` incompatible because it exceeds the 30-column ARC bound.

**Rejected alternatives.** The old family, palette, palette-kind, density, position-bias, and texture declarations were removed rather than retained as aliases or singleton controls. Content axes were not exposed because an exact public override would need a stable, observable representation and additional combinatorial legality rules.

**Evidence.** The override gate and parametrized task tests pass across all bands; invalid scalars, unknown names, and the declared incompatible pair fail deterministically.

## D4 — Use a seed-hashed canonical-support schedule

**Choice.** `schedule_profile` hashes task ID, version, seed, sample index, and difficulty; byte values below 64 select canonical support, giving an expected 25% rate without a short index period.

**Reason.** The profile floor needs regular canonical-size morphology, but a fixed four-step cycle is easy to correlate with sample position and requires exhaustive period claims.

**Rejected alternative.** A literal `sample_index % 4` schedule was tested and removed because it creates an avoidable periodic shortcut. No `LESSON_SCHEDULE_PERIOD` is declared.

**Evidence.** The final semantic sample observed 163 canonical-support and 437 broad draws; profile floor found 15/60 exact-profile hits and at least one per band. The regression asserts seed sensitivity and absence of short fixed periodicity.

## D5 — Reproduce canonical palette roles without copying scenes

**Choice.** Canonical-support draws choose the base pair from relation-label colors `(3,6,8)` and extra roles from the remaining palette, while shapes, orientations, placements, and exact color selection remain generated.

**Reason.** Earlier strict profile evidence showed no overlap with canonical input/output palette-role signatures despite lawful geometry.

**Rejected alternative.** Copying a canonical input or hard-coding a full canonical palette would inflate profile metrics and reduce diversity. Broad draws continue to sample four distinct colors from 1–8.

**Evidence.** `test_schedule_overlaps_canonical_palette_roles` and the final profile/semantic gates pass.

## D6 — Make validation structural and canonical-compatible

**Choice.** `self_check` parses actual color-9 frames, validates gallery membership, interior colors, overlap, and stray cells. `strict_canonical_like` delegates to this lawful-domain check.

**Reason.** A validator tied only to generator metadata can accept malformed scenes or reject canonical morphology. Structural validation also lets the semantic and override tools test returned pixels.

**Rejected alternative.** Requiring the generated 8/6/3 witness set inside `self_check` would wrongly reject lawful canonical inputs; that curriculum property is tested separately on generated draws.

**Evidence.** All five canonical inputs are accepted; malformed-grid regressions and 600/600 strict semantic samples pass.

## D7 — Declare the exact historical shortcut as a rival

**Choice.** Add the executable `fixed_position_template` rival, a `permuted_relation_positions` witness, and `lesson_identifiable` scoring over demonstrations and query.

**Reason.** Distribution diversity is not enough; a lesson must refute a plausible wrong rule before its query label is useful for training.

**Rejected alternative.** A prose-only warning cannot be enforced or included in source-bound census evidence.

**Limitation.** One rival does not enumerate every hypothesis a model might learn. The generic census also tested its available generic rivals, but the final claim remains finite and declared-rival scoped.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/5fdbbb5a53ef/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
