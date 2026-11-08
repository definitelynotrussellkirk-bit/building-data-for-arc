# Working notes: 5c0bcc9d1b8b

## Current rule and grammar

Count all gray (`5`) cells. Detect whether the two parallel divider lines are rows or columns. Rebuild those parallel walls at center ±1, retain the centered perpendicular black crossbar, and draw a centered gray line of the same count along the track. Inputs are odd square grids of size 9, 11, 13, or 19 with colors `{0,5,7}`.

The selected canonical Racket authority remains rule hash `326f0e0036c3`. The two selected solution records had stale `racket_target.target_code`; they now contain the exact canonical program. Their archival `raw_code` is preserved. `shared/data/canonical/puzzles.jsonl` was not changed.

## Reversed decisions

- **Prior choice:** fixed 11×11 scenes with four framing lines and 4–7 gray cells. **New choice:** the canonical three-divider track (two parallel walls plus one centered crossbar), all four canonical sizes, and canonical wall offsets. **Reason:** the prior generator rejected all eight labeled canonical inputs and represented a different puzzle family. Evidence: `checks/before/` versus `checks/after-v1/`.
- **Prior choice:** several linked/inert axes and degenerate textures. **New choice:** one finite exact `scene_profile` axis. **Reason:** the profile is recoverable from pixels, every override is testable, and no impossible Cartesian combinations are advertised.
- **Prior intermediate choice:** 26 profiles. **New choice:** 16 profiles (two gray counts × two directions × four sizes). **Reason:** the shared override checker probes finite enum domains of at most 16 values; the reduced domain remains complete for the intended distinctions and is now mechanically probeable rather than marked diagnostic.

## Distribution decisions

For each canonical size, ordinary generation omits that size's public-demo gray count:

- size 9: counts 7, 9 (canonical lookup would use 5)
- size 11: counts 7, 11 (canonical lookup would use 9)
- size 13: counts 9, 11 (canonical lookup would use 13)
- size 19: counts 13, 19 (canonical lookup would use 11)

Both directions occur at every size/count. Every emitted profile is therefore a direct counterexample to the strongest simple canonical-fitting rival, `canonical_size_to_count`. Generated motifs are four-connected; `self_check` accepts eight-connected motifs because one official 19×19 example is only diagonally connected. The centered crossbar may contain background inside the channel, matching that canonical example, but must remain zero outside the parallel walls.

Difficulty changes sampling weights, not legal support. Easy modestly favors the diverse 11×11/count-11 profiles; medium favors 11×11 and 13×13; hard favors 13×13 and 19×19. Every band retains all 16 profiles. Three demonstrations are required. Since every generated pair individually refutes the declared size-lookup rival, production and rotated-query lessons remain identifiable under that rival.

## Verification and retained tools

Final generator SHA-256: `53f5f7e97af156a6f8b03c78d151f9a3a93ee1003ade0e8783ec0a26c96eca1a`.

- Twelve-stage after battery: 12/12 green (`checks/after-v1/checks/5c0bcc9d1b8b_after_battery_summary.json`).
- Focused task tests: 42 passed, including canonical parity, all exact overrides, malformed inputs, scalar rejection, determinism, shortcut refutation, and lesson checks.
- Semantic gate: 600/600 strict generated inputs, 8/8 canonical inputs accepted, and 60/60 declared rival claims held.
- Lesson census: 300/300 lessons materialized, 1,200 pairs, 521 unique inputs, 0 ambiguous production queries and 0/1,200 ambiguous query rotations (`checks/lesson-census-final.json`).
- `workspace/probe_contract.py` exhausts all profiles and canonical pairs and retains an exact shortcut witness. Its three tests pass.
- Minimal counterexample: `counterexamples/size_lookup_gray_count.json`.

## Known limits and open findings

The generator intentionally covers a canonical-linked finite envelope, not arbitrary sizes, palettes, wall offsets, even gray counts, or off-center tracks. The 16-profile output codomain is deliberate and declared. Passing source-bound checks does not itself grant catalog approval; maintainer intake still decides approval. No unresolved task-local correctness blocker remains.
## Current reviewer considerations

Source SHA-256: `77c953876a13dee43aef7d3576d3dfcd53bab956ddd77a46c7a54f6db708aeef`.

# Decisions — `5c0bcc9d1b8b`

## D1 — Fail closed on invalid replay identity and difficulty scalars

**Observed baseline.** Generator SHA-256 `53f5f7e97af156a6f8b03c78d151f9a3a93ee1003ade0e8783ec0a26c96eca1a` accepted booleans, floats, and numeric strings as `seed`, and accepted booleans, numbers, or arbitrary strings as `difficulty`. Invalid difficulty values fell through `_PROFILE_CHOICES.get(..., SCENE_PROFILES)`, silently behaving like the default band. The baseline defect linter recorded 30 strict-scalar warnings across default/easy/hard probes. The original rationale for permissive fallback is not documented.

**Decision.** Require `type(seed) is int`; require `difficulty` to be exactly one of `None`, `"easy"`, `"medium"`, or `"hard"`. Reject bad values before constructing `GenCtx` or drawing any randomness.

**Alternatives rejected.** Coercing numeric strings/floats would make replay identities alias unexpectedly. Treating unknown difficulty as default hides caller errors. Validating only in `gen_ctx` would broaden a task-local repair into a shared runtime change without evidence that every generator is ready for it.

**TDD evidence.** `checks/tdd-red-invalid-difficulty.log` and `checks/tdd-red-invalid-seed.log` fail on the baseline behavior; the matching green logs pass after the minimal checks. An intermediate battery in `checks/after/` retained the remaining seed failure after difficulty was fixed. The final defect linter is clean in `checks/after-final/`.

**Failure mode/limit.** This deliberately rejects previously accepted invalid calls. It does not change the domain of any valid call.

## D2 — Preserve version, rule authority, and every tested valid output

**Decision.** Keep `VERSION = "5.0.0"`, `RULE_HASH = "326f0e0036c3"`, the 16 production profiles, sampling weights, and Racket authority unchanged. The repair is boundary validation, not a distribution or semantic revision.

**Probe.** `checks/legal-replay/report.json` compares the original packet source with the final source across 640 ordinary valid calls and 192 exact-profile override calls spanning all four difficulty values, five default seeds, 32 sample indices, and all 16 profiles. All **832/832** outputs match exactly.

**Alternative rejected.** Bumping the version would perturb valid RNG streams even though their intended semantics did not change; that would create unnecessary data drift and obscure the small repair.

**Self-review.** Because the only canonical-path change runs before `GenCtx`, it introduces no new visual shortcut or support restriction for valid inputs. The valid-call replay and full battery independently support that conclusion, while not claiming exhaustive equivalence over every integer seed/index.

## D3 — Prototype two nearby, structural rule parameters

**Decision.** Build a separate proposed family under `workspace/parametric/` with:

- `output_wall_offset ∈ {1,2}`, canonical default `1`;
- `length_measure ∈ {cell_count, track_span}`, canonical default `cell_count`.

The invariant reasoning remains recognizable: detect the track, summarize the gray motif, rebuild symmetric walls and the perpendicular crossbar, then compress the motif to a centered line. The first parameter changes output geometry; the second changes the executed summary statistic.

**Alternatives rejected.** Palette changes are mostly cosmetic. Input size, orientation, motif texture, and sampling weights already vary without changing the rule. Making orientation a hidden parameter would conflict with the visible track cue. Arbitrary program mutations would no longer be a nearby family.

**Canonical preservation.** Setting `(1, cell_count)` reproduces all 8 labeled canonical pairs under exact Racket execution. The production generator and selected canonical rule remain fixed.

## D4 — Choose the hidden setting once per episode and make demonstrations decisive

**Decision.** Select one complete setting as `ALL_SETTINGS[seed % 4]`, then use it for all three demonstrations and the query. Use four fixed production profiles whose gray-cell count exceeds their longitudinal track span, so both length measures differ; include both track orientations and several sizes. Public challenges omit setting values, Racket source, and query answers.

**Probe.** `checks/parametric/wall-offset-length-measure-seed17-final.json` records all four complete settings. Every pair matches its exact materialized Racket program, all four settings produce distinct outputs on the retained witness, and every demonstration refutes all three alternative settings. Six focused prototype tests passed as part of the 56-case portable task suite.

**Failure modes guarded.** The tests catch per-pair rule resampling, missing/incorrect Racket materialization, leakage into public challenges, canonical-default drift, Python/Racket disagreement, and demonstrations that leave a parameter rival alive.

**Limits.** Evidence covers one deterministic episode seed and four chosen profiles per setting, plus full canonical replay for the default. It exhausts only the declared four settings, not unrelated rival rules. `track_span` is a nearby proposed label, not claimed to be an original ARC answer.

## D5 — Keep the parametric family proposed and outside the canonical execution path

**Decision.** Do not alter the production `generate(...)` API, catalog kind, selected Racket rule, or approval metadata. Retain exact Racket files, public examples, tests, and evidence under the task-local prototype workspace.

**Reason.** The packet asks for authoring evidence, not a new shared parametric runtime or variant approval. Mixing hidden-rule variants into a generator whose labels are bound to one canonical rule would break authority guarantees.

**Integration boundary.** A future shared intake must independently decide variant naming, training admission, episode API, and rule-hash registration. `FEEDBACK_TO_CODEX.md` proposes a common verification harness rather than silently inventing those interfaces here.

## D6 — Record orientation as contextual gating, not multi-step composition

**Assessment.** Parallel-divider orientation determines whether the reconstruction and gray line are vertical or horizontal. `checks/curriculum/orientation-gating.json` uses two exact production profiles and live Racket outputs: an always-horizontal rival fails the vertical scene and an always-vertical rival fails the horizontal scene.

**Annotation decision.** Mark `contextual_gating` present with support scope `generated_input`. Mark `sequential_state` and `multi_rule_interaction` not applicable: the output is computed from input features, not from an intermediate state or interacting independent rules. Leave `task_defined_symbols` unknown rather than overclaiming that ordinary ARC color roles constitute a special learned-symbol mechanism.

**Limit.** The two-profile witness establishes a real prediction-changing gate, not corpus-wide mastery or exhaustive coverage.

## D7 — Retain the existing three-demonstration lesson policy and verify it at scale

**Decision.** Keep `EXAMPLES_NEEDED = 3` and the existing declared rival `canonical_size_to_count`. Every ordinary production input individually refutes that rival, so no new schedule is necessary.

**Evidence.** The final source-bound census materialized 300/300 lessons (100 per band), 1,200 pairs, and 521 unique exact inputs. With three ordered demonstrations and one query, it found 0 production ambiguities and 0/1,200 ambiguous query rotations under the required rotation policy (`checks/lesson-census-20261020-final.summary.json`).

**Limit.** This is finite evidence against the declared/generic rivals, not proof that every conceivable solver infers the intended rule.

## D8 — Treat both peer targets as findings-only audits

The audit targets were not part of the selected repair scope. I reproduced their current source-bound defects and left them unchanged:

- `1409f5f7af2e`: no generated shared-endpoint target chains in 8,000 sampled inputs, enabling a shortcut that fails 3/5 canonical pairs;
- `e15a71a2526e`: exact `n_interior_8s=5` silently clamped to 2 for a lawful advertised joint request.

Details and reusable evidence are in `AUDIT.md` and `checks/audit/`. No audit finding is presented as a repair or approval.
