# Working notes: a3c33cc348fb

## Current rule and domain

A calibrated input contains one solid two-color framed rectangle and one cyan marker outside it, aligned with an inclusive rectangle row or column. The output expands the rectangle-marker bounding box, keeps the original frame color on the new perimeter, fills the strict interior with the original inner color, consumes cyan, and clears everything outside the expanded box.

Selected generator version: `3.1.0`. Final source SHA-256: `fc9d54b672dcf95bf69009b7592d5793033df45d073c0c208ad05d4c16c1d478`. Canonical `RULE_HASH` remains `b3185fa9390c`; the canonical Racket rule itself was not changed.

## Decisions in this review

- Reject non-literal-integer `seed` and `sample_index` values and reject negative sample indices before constructing `gen_ctx`. This closes the strict defect-lint failures without changing valid calls.
- Keep all eight reach profiles, but give public-family draws a deterministic 50% canonical-scale branch over `(11,11)`, `(13,12)`, and `(13,13)`. Exact public overrides still return the official literal inputs. The final pinned profile audit found exact support `7/20`, `10/20`, and `9/20` in easy/medium/hard, with `26/60` exact and `29/60` envelope hits.
- Declare and execute the plausible `marker_line_only` shortcut. `full_bbox_repaint` is its witness, and `lesson_identifiable` rejects any three-demonstration lesson that leaves the rival alive.
- Synchronize the two selected base-solution `target_code` fields to the exact canonical text through the hash-bound authority-sync tool. Their historical minified `raw_code` remains unchanged as archival source; both forms execute identically on all canonical pairs.
- Keep the proposed rule parameter separate in `workspace/parametric/`: `expansion_mode` is sampled once per episode as canonical `bbox` or alternate `corridor`. It is not selected for production or approval.

## Evidence and limits

The strict after battery is 12/12 green. The required-rotation semantic gate is green, and the source-bound census materialized 300 lessons with three demonstrations plus one query, checked all 1,200 query rotations, and found zero ambiguities against the declared rival; this is finite rival evidence, not universal identifiability. The parametric prototype executed both exact Racket programs on two episodes, matched 16/16 Python cross-checks, and refuted the alternate setting in all eight query rotations.

The new portable tests pass `21/21`. The aggregate `task_tests` stage remains blocked before execution by the packet's untouched frozen fixture, which uses a fixed `__file__.parents[...]` canonical path. That fixture's SHA-256 remains `4747d20d8a1fae402e51d4b806d421a740aec541591e89cd92e00f30930c73ae`; migration belongs to the library maintainer.

## Current owner source and evidence limits

Accepted version3.1.0 strict scalar guards, canonical-scale sampling and an executable marker_line_only rival/full_bbox_repaint witness. Exact public profile overrides remain literal. Two selected target fields equal unchanged canonical text, with archival raw_code preserved. Reviewer reports12 green stages,21 new focused tests,26/60 exact and29/60 envelope support,600/600 lawful draws and300 lessons/1200 clean rotations with1199 unique inputs. Aggregate task tests remain blocked before pytest by the unchanged fixed-depth frozen fixture. The bbox/corridor prototype has2 episodes,16 Racket/mirror matches and8 clean alternate-setting rotations;default bbox is exact canonical source. Its report predates the unrelated4f065093e631 ledger optimization:historical whole-ledger SHA remains provenance,the a3c33cc348fb program and labels are unchanged. Owner checked hashes and public projections statically,not new prototype execution. No full aggregate pass,variant approval,production parameter API or training admission.
## Current reviewer considerations

Source SHA-256: `fc9d54b672dcf95bf69009b7592d5793033df45d073c0c208ad05d4c16c1d478`.

# Decisions for a3c33cc348fb

## D1 — Preserve the canonical rule

**Choice.** Keep the canonical full-bounding-box transformation and `RULE_HASH=b3185fa9390c` unchanged.

**Rationale.** Rule smoke and execution parity already showed correct canonical behavior. The baseline failures were API validation, distribution support, teaching metadata, and exact authority text—not wrong labels.

**Alternative rejected.** Replacing the canonical program with the corridor rule would change the ARC task. The corridor behavior is retained only as a proposed hidden parameter and semantic rival.

**Failure mode / limit.** Passing canonical examples does not prove generated lessons identify the rule; that is addressed separately by executable rivals and lesson tests.

## D2 — Validate scalar calls at the public boundary

**Choice.** Require `type(seed) is int`, `type(sample_index) is int`, and `sample_index >= 0` before `gen_ctx` construction.

**Rationale.** The baseline strict defect linter reproducibly found 33 invalid-call acceptances, including booleans, floats, strings, and `-1`. These values are not part of the documented sampling contract.

**Alternative rejected.** Coercing values with `int(...)` would make replay identities ambiguous and would continue accepting booleans. Allowing negative indices would leave an undocumented coordinate in the deterministic sample space.

**Probe.** `tests/test_repair_contracts.py` first failed on all 11 representative invalid values and now passes.

## D3 — Add canonical scale without copying only canonical instances

**Choice.** On non-overridden public-family draws, choose a separate deterministic `canonical_scale` branch with probability 0.5 and render onto one of the three canonical `(height,width)` shapes. Keep D4 transforms, colors, placements, and all generalized profiles.

**Rationale.** The baseline pinned audit produced only `2/60` exact and `7/60` envelope hits, including zero exact support in medium and hard. The selected change repairs the scale distribution while preserving the relationship grammar and diversity.

**Alternatives rejected.** Always returning literal official inputs would overfit and sharply reduce diversity. Raising every generated canvas to canonical size would erase useful smaller/larger contrasts. Changing the profile scheduler alone would not guarantee canonical dimensions.

**Measured outcome.** Final pinned counts are easy `7/20`, medium `10/20`, hard `9/20` exact; pooled `26/60` exact and `29/60` envelope, with no crashes.

**Failure mode / limit.** The 50% branch is an engineering calibration, not an estimated natural ARC frequency. The finite floor audit does not characterize every seed.

## D4 — Teach against a concrete plausible shortcut

**Choice.** Declare `marker_line_only` in both semantic and lesson competitor registries, pair it with `full_bbox_repaint`, and make `lesson_identifiable` require a labeled demo to refute it.

**Rationale.** The baseline had no semantic contract. Connecting the marker to the rectangle without repainting the full box is a concise, executable alternative that preserves most visible object roles and therefore represents a useful shortcut to test.

**Alternatives rejected.** Generic color-only or first-object shortcuts are less task-specific and are already searched by the shared census. A rival that ignores alignment entirely is too weak because one example refutes it trivially.

**Lesson policy.** Three labeled demonstrations and one query. Downstream query rotation is supported, so the required-rotation gate and `--rotate-query` census were run rather than treating order as fixed.

**Measured outcome.** `300/300` production lessons and `1200/1200` held-out rotations have no declared-rival ambiguity. This is not proof against undeclared hypotheses.

## D5 — Synchronize only selected authority text

**Choice.** Use the supported hash-bound authority-sync workflow to replace only the two `racket_target.target_code` values with byte-exact canonical text. Preserve `raw_code` unchanged.

**Rationale.** Baseline execution parity passed, but strict authority sync failed on exact text divergence. `target_code` is the selected execution authority; `raw_code` is historical source and should remain auditable.

**Alternative rejected.** Reformatting or deleting `raw_code` would erase archival provenance. Hand-editing without a proposal/apply receipt would lose source-hash binding.

**Measured outcome.** Final authority sync passes; canonical and target exact SHA-256 are `37c7b932...`, while both archived minified forms remain semantically equivalent and separately reported.

## D6 — Choose `expansion_mode` as the bounded rule parameter

**Choice.** Prototype `expansion_mode ∈ {bbox,corridor}`, sampled once per four-pair episode, with `bbox` as the byte-exact canonical default.

**Rationale.** Both settings preserve the framed rectangle, cyan marker, axis alignment, color roles, and the central question of how the rectangle reaches the marker. They differ on a visible structural consequence in every lawful input, so demonstrations can identify the hidden setting.

**Alternatives rejected.** A marker-color-dependent rule would change a fixed semantic role. A distance threshold is primarily an input-distribution parameter unless it changes behavior discontinuously, which would add complexity without a cleaner teaching contrast. Frame-thickness changes introduce a second geometric convention and were not needed.

**Evidence.** Two setting-specific episodes, 16 real-Racket applications plus two canaries, 16 Python mirror matches, and eight query rotations all refuting the alternate setting.

**Failure mode / limit.** Only two settings and one declared alternative are tested. The prototype is proposed authoring evidence, not a production API or approval claim.

## D7 — Respect the frozen-fixture boundary

**Choice.** Leave `tests/test_generator_a3c33cc348fb.py` byte-identical and put all new coverage in two portable test files using `reviewer_support`.

**Rationale.** The duties explicitly designate the baseline fixture as frozen. Its fixed parent-depth canonical lookup fails in the portable task-test snapshot, but changing it would cross the review boundary.

**Measured outcome.** New tests pass `21/21`. Aggregate task-test preflight remains blocked before execution and is reported as such.

**Maintainer action.** Migrate the inherited fixture to `find_root(__file__)`, `canonical_path`, and `canonical_pairs`, then rerun the aggregate task-test stage.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a3c33cc348fb/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
