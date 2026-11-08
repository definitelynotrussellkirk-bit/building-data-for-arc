# Generator notes: 17b0b2791dd2

## Current rule and domain

Recolor every blue 4-connected component whose normalized shape is **exactly** a three-cell vertical line from blue (1) to red (2). Leave all other blue components unchanged. Version 2.0.0 generates 8–14 by 8–14 grids containing 1–3 separated vertical-three targets, one horizontal-three orientation negative, and one vertical-four exact-length negative.

The canonical authority remains unchanged at rule hash `1deed242f221`. Canonical inputs are accepted even when they do not contain the generated vertical-four witness; the stronger witness is a training-distribution guarantee, not an authority restriction.

## Reversed decisions

The 1.3.1 source exposed nine public controls, difficulty-dependent subranges, degenerate textures, and optional random distractors. Its comments suggest those choices were intended to add variety, but the task had no prior current-design note; the actual battery showed dead or misleading axes, non-exact overrides, and no executable lesson contract. Two retained audits against baseline SHA-256 `6346ce7912287d0df59266ec6c6c717d0c91cbe42f0a331611e0bf1ffc68b3cd` also found a complete medium lesson at seed 1, sample indices 0–3, with no non-target tall vertical object, so “recolor every tall component” survived all demonstrations.

Version 2.0.0 reverses those choices:

- Public axes are only the three independently observable controls: `grid_h`, `grid_w`, and `vertical_count`.
- Every advertised value is legal in every difficulty band and is recovered exactly by `observe_overrides`.
- H3 and V4 negatives are mandatory in every ordinary draw instead of optional distractors.
- Randomized constructive backtracking places all components with one-cell 4-neighbor separation; generation fails loudly rather than silently weakening the grammar.
- `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable` make the teaching claim executable.

The minimal baseline lesson reproducer is `counterexamples/review-245186fe904dc04d-v0001/vertical_exactness_lesson.json`; its regression is `tests/test_generator.py::test_retained_seed_one_regression_cannot_omit_the_exactness_witness`.

## Final evidence

Final generator SHA-256: `6103d5e3fc948a2b3fea5f0c842a4f82fe4ea6ab1752009a1d4867af731fb91f`.

- Task-local tests: 47 passed, 0 failed/skipped/errors.
- Twelve-stage after battery: 12 green.
- Override matrix: 9,990/9,990 accepted draws, 111 cases across easy/medium/hard, 0 findings and 0 warnings.
- Lesson census: 300 three-demonstration/one-query bundles (100 per band), 1,200 unique inputs, 0 production ambiguities and 0 ambiguities across 1,200 query rotations against the declared rivals.
- Post-repair visible-only solve: all three demonstrations passed on the first revision; earlier rule exposure was declared and no reference was consulted during the solve.

## Known limits and open findings

The semantic evidence is finite and covers only declared rivals; it is not a proof of unique induction against every possible hypothesis. The generated grammar intentionally uses only separated line components in fixed colors 0/1, so it does not train arbitrary blue shapes, touching components, or palette-role generalization. No Racket authority change is proposed.

## Current scoped audit assessment

`evidence/current-audit-assessment.json` explicitly resolves the two prior omitted-negative/dead-control findings against the accepted current source. Checks are finite and reviewer-reported, not an owner rerun.
## Current reviewer considerations

Source SHA-256: `6103d5e3fc948a2b3fea5f0c842a4f82fe4ea6ab1752009a1d4867af731fb91f`.

# Decisions: 17b0b2791dd2

## D1 — Make exact-length evidence unconditional

**Prior choice.** Version 1.3.1 always placed at least one V3 and H3, then drew 0–2 optional distractors from a five-shape pool. The source comment says this was intended to exercise more stay-blue shapes, but no current design note documented why lesson-critical evidence remained optional.

**Failure.** Baseline seed 1, medium indices 0–3 formed a complete four-pair lesson with no V4 or other non-target tall component. “Recolor every component whose bounding box is taller than wide” matched all labels. See G1 in `REVIEW.md` and the exact replay in `repo/generators/17b0b2791dd2/counterexamples/review-245186fe904dc04d-v0001/vertical_exactness_lesson.json`.

**New choice.** Every ordinary draw contains one V4 exactness negative and one H3 orientation negative in addition to 1–3 V3 targets.

**Rejected alternatives.** Increasing distractor probability or lesson size still leaves nonzero ambiguity probability; rejecting ambiguous lessons after sampling adds avoidable retries and makes support harder to reason about. Constructive inclusion is cheaper and deterministic.

**Probe/failure mode.** `test_retained_seed_one_regression_cannot_omit_the_exactness_witness` replays the historical window and checks that the tall rival disagrees on every generated pair. Remaining risk is an undeclared rival not covered by the finite contract.

## D2 — Remove controls that are not honest independent axes

**Prior choice.** The baseline declared nine keys: dimensions, count, palette/texture aliases, singleton palette/color/bias/density fields, and degenerate textures. Difficulty branches narrowed dimensions and counts below advertised ranges.

**Failure.** The before override stage reported 6,590 findings, including 4,860 mismatches and 1,710 generation errors; lint/defect lint also reported missing `RULE_HASH`, dead/singleton axes, and texture-domain problems.

**New choice.** Public axes are exactly `grid_h: 8..14`, `grid_w: 8..14`, and `vertical_count: 1..3`. Every value is valid in every band, recoverable from the grid, and strict about types/ranges/unknown keys.

**Rejected alternatives.** Keeping singleton controls as metadata creates the appearance of distribution coverage without changing inputs. Keeping `texture` as a palette alias is especially misleading because all lawful cells must stay blue under this task’s rule.

**Probe/failure mode.** Boundary combinations are tested in all four difficulty values; the final override checker accepted 9,990/9,990 draws. The remaining combinatorial space is small enough that the public contract is easy to audit.

## D3 — Use constructive backtracking with separation

**Choice.** Build the required shape multiset first, then place components by randomized backtracking with one-cell 4-neighbor guards.

**Rationale.** This makes object identity, exact component counts, and semantic witnesses true by construction. It also eliminates the baseline’s probabilistic whole-layout retry behavior and accidental component merging.

**Alternatives considered.** Repeated `place_no_overlap` calls are simpler but can wedge later objects and require probabilistic resets. A fixed template would be reliable but reduce positional diversity.

**Probe/failure mode.** Generation self-checks and recovers all overrides before returning. The smallest 8×8, three-target combination is exercised explicitly. A future grammar expansion should add a failing placement test before adding shapes.

## D4 — Preserve canonical support without narrowing defaults to canonical sizes

**Choice.** A seven-profile schedule strongly weights canonical-like dimensions/counts, while each draw still includes the complete declared domain in its choice support. Difficulty changes the profile offset, not legality.

**Rationale.** The profile floor needs reliable canonical support, but override semantics should not depend on difficulty. Final profile-floor evidence found exact canonical-profile hits in every band (18/60 total).

**Rejected alternative.** Separate difficulty-specific min/max ranges caused the baseline’s exact override rejections and made the same documented axis mean different things in different bands.

**Limit.** Weighted finite samples demonstrate support, not a uniform distribution. The distribution intentionally favors a small canonical-like profile schedule.

## D5 — Separate authority grammar from training-distribution guarantees

**Choice.** `self_check` accepts lawful canonical examples containing V3 and H3 even when V4 is absent; `generate` additionally guarantees V4 for teaching exactness.

**Rationale.** Requiring V4 in the validator would incorrectly reject canonical authority inputs. Conversely, allowing generation to omit V4 would recreate G1.

**Probe/failure mode.** Canonical pairs pass `self_check` and the independent Python oracle matches all labels. Generated draws separately assert `_has_vertical_four`.

## D6 — Declare executable semantic competitors

**Choice.** The generator exposes two pure rivals: recolor every vertical line and recolor every three-cell component. Named witnesses and `lesson_identifiable` must refute them across the demonstrations.

**Rationale.** Correct per-grid labels do not guarantee that a complete training lesson teaches the intended rule. Making rivals executable lets the battery and census test the curriculum rather than only input legality.

**Alternative.** Text-only notes are cheaper to write but cannot be mechanically checked and were absent in the baseline.

**Limit.** These are plausible high-value rivals, not an exhaustive hypothesis class.

## D7 — Leave the Racket authority unchanged

The canonical rule and outputs already express the intended exact V3 transformation. `rule_smoke`, `racket_lint`, and `authority_sync` all pass after the Python-only repair, so changing authority code would add risk without correcting the generator defect.

## D8 — Treat the two assigned audits as findings-only

`0eb4eaa46003` has a reproduced in-domain teaching shortcut. `ebe910be6876` has a generated-domain restriction that permits a rival but an authority counterexample outside its validator. Per assignment, neither audited source was modified; evidence and scope are recorded in `AUDIT.md`.

## Parametric admission review — `review-778e2a1a9f50a04c`

### D9 — Add a relational alternative instead of a cosmetic selector toggle

The native family keeps `target_policy=exact_vertical3` byte-identical to the canonical Racket program and adds `nearest_horizontal3`. In the alternative, exact vertical triples are selectors; each selector chooses the exact horizontal triple with minimum cell-to-cell Manhattan distance, breaking ties by candidate reading order. The output recolors the union of selected horizontal triples. This creates a genuine input-dependent selector-to-target relation rather than a remap that could collapse into a direct shape predicate.

### D10 — Preserve selector multiplicity in the intermediate

Stage A emits the ordered candidate-index vector with one entry per selector, including duplicates. Stage B consumes that vector and paints the referenced candidate union. Retaining duplicates makes the intermediate describe the actual selector assignment even though rendering the union is idempotent. The qualified witness has true indices `[1, 5, 5]`; replacing them with the first-N shortcut `[0, 1, 2]` changes nine protected-Racket output cells.

### D11 — Construct demonstrations against a finite shortcut inventory

The first two demonstrations distinguish the canonical and relational settings while refuting nine named alternatives covering indiscriminate line recoloring, fixed candidate choice, nearest-by-anchor variants, source-order shortcuts, and selector/candidate count shortcuts. The retained bounded audit checked 48 requests, 368 inputs, demonstration counts 2/3/6, four sequential queries, 24 protected-Racket executions, and found no harmful survivor. This is finite evidence, not a uniqueness proof.

### D12 — Keep production authority unchanged

The approved production generator remains SHA-256 `6103d5e3fc948a2b3fea5f0c842a4f82fe4ea6ab1752009a1d4867af731fb91f`. The default parametric setting returns canonical program SHA-256 `1deed242f2217b9fd4d8efd268961d2c06dd79e19892aac216878a5231010886`. Native qualification and reviewer witness replay passed, but owner integration, fresh acceptance replay, and any training-admission decision remain pending.

