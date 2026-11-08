# Working notes: 1a92a12bac06

## Intended rule and lawful generator domain

The canonical rule is pinned by `RULE_HASH = "6d628a0b1a7d"`: find each 4-connected red (`2`) object, measure its vertical extent, and recolor the object's bottom `floor(height / 2)` rows cyan (`8`). Grid shape and all other cells are unchanged.

The selected v3 generator deliberately samples a narrower canonical bar grammar: 3–4 separated, one-cell-wide vertical red bars on a zero background. Default sample indices cycle through bottom-aligned, floating, mixed-anchor, and top-aligned profiles. Every sample has both odd and even bar heights. Exact public axes are `grid_h` (7–14), `grid_w` (9–13), `n_bars` (3–4), and `texture` (the four profiles above). The generator does not claim coverage of arbitrary wide or irregular red components accepted by the Racket authority.

## Decisions in this review

The prior approved source `841808457e0df267dd807319c83f015efa4a28772704ec4b4f73e0c5592f4859` already had strong distribution, profile, override-axis, and declared-rival support, so production sampling was left unchanged. Prior return `review-224dbceb721d0d34:v0001` was used only as a lead; all final measurements were rerun against this packet.

A newly exposed API defect accepted invalid scalar call arguments. `generate()` now requires an exact integer `seed`, an exact non-negative integer `sample_index`, and `difficulty` in `{None, easy, medium, hard}` before processing overrides. Five pinned valid calls remain byte-identical. Final generator SHA-256: `45d7191f37ffec706ce96b767acae52115b7b0b037cf138168b3486d2690c504`.

Two selected authority records had behavior-equivalent but text-divergent `racket_target.target_code`. Manual review synchronized only those selected `target_code` pointers to the exact canonical program SHA-256 `5830ead864bfe68f65a74f820cae70f35764f0ef9c8d5b18dd7848fe5c06d6cb`. Their archival `raw_code` remained byte-for-byte unchanged at SHA-256 `c7f7f1807cfc2af34336428b2f5c3f1af4a1acdcefebd4cf01ffa222939b2399`. The canonical ledger program itself did not change.

## Parametric prototype

`workspace/parametric/` contains an isolated, runnable proposal with episode-fixed parameters `fill_side ∈ {bottom, top}` and `rounding ∈ {floor, ceil}`. The canonical default is exactly `bottom+floor`; prototype code is not wired into production generation. All four exact Racket programs matched an independent Python mirror, and every rival setting was distinguished by each retained episode's three demonstrations. Evidence: `checks/parametric/evidence.json`.

## Verification and limits

- Final after battery: 12/12 green.
- Portable selected task tests: 67/67 passed.
- Scalar regression: 16 invalid classes rejected; five valid output pins unchanged.
- Source-bound lesson census: 300/300 lessons and 1,200/1,200 query rotations, zero declared-rival ambiguity, zero scoring/materialization errors, 1,184 unique inputs.
- Fresh post-repair visible solve: 3/3 demonstrations in one revision, with earlier exposure declared and no reference consultation during the solve.

These are finite checks against the declared rivals and sampled schedules, not a proof of unique induction against every possible hypothesis. No unresolved task-local blocker remains.
## Current reviewer considerations

Source SHA-256: `45d7191f37ffec706ce96b767acae52115b7b0b037cf138168b3486d2690c504`.

# Decisions: 1a92a12bac06

Final generator SHA-256: `45d7191f37ffec706ce96b767acae52115b7b0b037cf138168b3486d2690c504`. Canonical selected Racket source SHA-256: `5830ead864bfe68f65a74f820cae70f35764f0ef9c8d5b18dd7848fe5c06d6cb`; declared rule hash: `6d628a0b1a7d`.

## D1 — Preserve the existing v3 production distribution

**Input choice.** Keep the existing four-profile schedule and lawful bar grammar unchanged: bottom-aligned, floating, mixed-anchor, and top-aligned examples, with odd/even bar heights and a scheduled canonical-profile pulse.

**Rationale.** The before battery already showed the current sampler passing distribution, profile-floor, semantic, diversity, override, grammar, and rule-smoke gates. The source-bound final census then materialized 300 lessons with 1,200 pairs and 1,200 held-out-query rotations, finding no ambiguity against the declared rivals and 1,184 unique inputs. Changing the sampler while repairing unrelated API/authority defects would create unnecessary regression risk.

**Alternatives rejected.** I did not broaden inputs to wide or irregular red components merely because the authority can process them; that would change the task curriculum rather than repair this selected generator. I also did not randomize the deterministic profile cycle, because witness frequency is weaker than guaranteed witness placement in assembled lessons.

**Probe and limit.** Evidence is in `checks/after/` and `checks/lesson-census.summary.json`. The census is finite and tests only declared rivals under the production sampler and permitted query rotations; universal identifiability remains unknown.

## D2 — Reject invalid call scalars at the generator boundary

**Defect.** After selected authority synchronization removed the first defect-lint blocker, the checker exposed 48 `strict-scalar` warnings across three probe bands. `generate()` accepted booleans, floats, and strings as `seed`/`sample_index`, accepted negative `sample_index`, and silently treated invalid `difficulty` values as the default band.

**New choice.** Add `_validate_call()` before generator-context construction. Require `type(seed) is int`, `type(sample_index) is int`, `sample_index >= 0`, and `difficulty` in `(None, "easy", "medium", "hard")`; then invoke the existing exact override validation.

**Why at this boundary.** The invalid values originated at the public call interface. Validation inside later schedule or RNG helpers would preserve partial coercion and make error behavior depend on which branch executes.

**Alternatives rejected.** Converting with `int(...)`, accepting bool as an integer, clamping negative indices, or falling back from an unknown difficulty were rejected because they make caller mistakes produce valid-looking but unintended data.

**TDD evidence.** The 16 focused cases failed before implementation (`checks/scalar-contract/red-pytest.log`), then passed after the minimal change (`checks/scalar-contract/green-pytest.log`). `checks/scalar-contract/after.json` shows all 16 invalid classes rejected and all five pinned valid grids byte-identical to their before hashes. The full task suite is 67/67.

## D3 — Synchronize selected authority pointers, preserve archival source

**Defect.** Two selected base-solution records used a behavior-equivalent `target_code` spelling based on `apply min/max`, while canonical selected execution used `min-list/max-list`. The guarded synchronization tool correctly refused automatic application because token sequences differed, even though all three sources solved all four canonical pairs.

**New choice.** After manual semantic and pointer-scope review, replace only `/racket_target/target_code` in:

- `shared/data/base/solutions/augmented/ce9e57f2__b27499621ef7.json`
- `shared/data/base/solutions/training/ce9e57f2__1a92a12bac06.json`

with the exact canonical program.

**Preservation requirement.** Both `/racket_target/raw_code` values remain byte-for-byte unchanged at SHA-256 `c7f7f1807cfc2af34336428b2f5c3f1af4a1acdcefebd4cf01ffa222939b2399`. The canonical ledger was not edited. The final authority status is therefore `selected_synchronized_archival_divergent`, not “all source copies identical.”

**Alternative rejected.** Rewriting archival `raw_code` or changing canonical code to the beautified variant would erase provenance or move authority without semantic need.

**Evidence.** `checks/authority-manual-review/review.json` binds before/after file hashes, changed/preserved JSON pointers, canonical execution evidence, and raw-code preservation. Final `authority_sync` and rule smoke are green with execution parity PASS.

## D4 — Keep the parametric extension isolated from canonical production

**Priority assessment.** The task supports two small, coherent rule parameters without changing its object roles or core reasoning:

1. `fill_side`: recolor from the bottom or top end of each bar.
2. `rounding`: use floor or ceil for half of an odd bar height.

The original rule is exactly `bottom+floor`.

**New artifact.** Build a runnable proposal under `workspace/parametric/` rather than altering `generate()` or selected authority. Each episode selects one setting, materializes its exact Racket program, and uses the existing lawful input sampler. Every pair contains both odd and even heights, so rounding is observable; off-floor bars make top/bottom behavior object-relative rather than canvas-relative.

**Why isolated.** Passing prototype evidence does not approve a new task family or change the canonical answer. Keeping it outside the selected execution path lets maintainers review the extension separately.

**Evidence.** `checks/parametric/evidence.json` contains four episodes, exact program hashes, public challenges, live-Racket/Python parity, and rival checks. For every chosen setting, all three demonstrations distinguish every other setting. Tests were written first: the prototype test initially failed because the module did not exist, then all five prototype tests passed.

**Limits.** Only the 2×2 parameter grid and retained bar grammar were tested. No claim is made for arbitrary red shapes, parameter compositionality beyond these four programs, or learner behavior outside the explicit counterfactual checks.

## D5 — Treat the fresh solve as exposed, not blind

The required post-repair solve was prepared only after generator and authority work. I closed source/rule/reference files from preparation through finish, solved from the visible examples, and obtained 3/3 in one revision. Because the rule had been seen earlier in the review, `earlier_rule_exposure` is honestly `yes`; `reference_consulted_during_solve` is `false`. The separate pre-work blind task remains recorded as earlier exposure `no`.

## D6 — Use prior review evidence only as a lead

The current review index identifies `review-224dbceb721d0d34:v0001` for source SHA `841808457e0df267dd807319c83f015efa4a28772704ec4b4f73e0c5592f4859`. I used it to understand the intended v3 schedule and existing probes, but did not treat its claims as current measurements. The before battery, repaired after battery, portable tests, parametric execution, authority review, lesson census, and solve were all rerun in this packet.

## D7 — Do not manufacture composition

This task remains a single objectwise operation repeated independently over bars. I did not add artificial sequential state, contextual gates, or multiple interacting rules simply to increase formal complexity. The parametric proposal changes a small episode-level operation choice while preserving the same component detection and height-measurement reasoning.

## 2026-10-24 — native half-fill relay review `review-55c9b88b279e2d1f`

The exact canonical program remains the `half_only` default. The new native
`largest_relay` setting applies the canonical bottom-half fill, recomputes
four-connected cyan networks, then paints the remaining red bar tops touching
the unique largest post-fill network yellow. This is a real A→intermediate→B
dependency: newly cyan bar bottoms change network membership and ranking before
B chooses its target.

The first two demonstrations were strengthened after bounded Racket audits
found side-only and original-feature shortcuts. They now place selected relays
on opposite physical sides and contrast a taller/smaller-connector winner with
a shorter/larger-connector winner, without increasing the two-demo minimum.
The retained audit covers both settings, seeds 0/17 and 2/3/6 demonstrations;
108 declared rival attempts leave no harmful survivor in that finite set.

Current evidence: `workspace/parametric/evidence/current/`, source inventory
`workspace/parametric/evidence/manifest.json`, native qualification
`WORK/checks/1a92a12bac06/qualification/qualification.json`, and protected
wrong-intermediate replay `WORK/checks/1a92a12bac06/causal/witness.json`.
Reviewer status is ready/qualified only. Exact-source owner acceptance and any
training admission remain pending.
