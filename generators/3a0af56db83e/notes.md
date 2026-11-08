# Working notes: 3a0af56db83e

## 2026-10-04 review (`review-e6563d790feff771`)

Baseline generator SHA-256: `a253a0e52e7ea00a83a5462589a752a757f1b9fb2d2494fe428ec97d4029298a` (version `3.0.0`). Final generator SHA-256: `ee0823fa1e8b2781c8a5425b44a87a7af69d66240a01433881caf02594476c6a` (version `3.1.1`). The selected Racket authority and `RULE_HASH=d5832237956b` were unchanged.

The prior return `local-random-6a9c88607f86` was used as a lead. Its current associated notes established two important facts: construct overlaps in the common projected 3×W frame, and permute the canonical color set to refute the canonical fixed-color shortcut. Those repairs were present in the immutable baseline and were remeasured rather than assumed.

### Finding and repair

The baseline battery was 12/12 green, but each generated scene reserved pairwise witnesses and then filled almost every remaining coordinate with one profile-wide overlap arity. As a result, no scene contained both three-way and four-way conflicts. Plausible rules that use the intended priority except on one overlap multiplicity could therefore survive a lesson whose query introduced that multiplicity.

Version `3.1.0` added explicit three-way and four-way witnesses, declared `reverse_on_three_way` and `reverse_on_four_way` rivals, and made every generated scene contain projected arities 0, 1, 2, 3, and 4. Free coordinates now mix the adjacent arities around each profile target—`0/2` for sparse, `1/3` for canonical, and `2/4` for dense—while preserving the exact mean foreground count, so `observe_overrides` remains exact.

A required 100-per-band source-bound census then exposed one rotated lesson in which `max_color_overlay` survived: seed `1911857371`, hard samples 61 and 63 both drew physical palette `(8,5,2,4)`, the unique assignment whose descending numeric colors exactly follow physical priority `(0,1,3,2)`. Version `3.1.1` excludes that one varied assignment. The regression uses the production sampler's actual same-seed/consecutive-index assembly; earlier task-local probes incorrectly changed seed between examples and were corrected.

### Final evidence

- Full after battery: 12/12 green (`checks/after/checks/3a0af56db83e_after_battery_summary.json`).
- Focused portable task tests: 24/24 passed (`checks/task-tests/`).
- Lesson census: 300/300 materialized, 900 unique inputs, 0 ordinary ambiguities and 0/900 ambiguous query rotations (`checks/lesson-census-final.json`).
- Semantic gate: 600 draws, strict-canonical 153/600, 11/11 witnesses firing, 11/11 rival claims verified, 12/12 smoke lessons identifiable.
- Override gate: 5,940/5,940 accepted across 66 cases and three bands.
- Exact fixed-color counterexample and Racket output: `checks/shortcut/3a0af56db83e-final/counterexample.json`.
- Reusable same-seed lesson/distribution probe: `workspace/overlap_arity_probe.py`.

### Limits

These checks cover the declared rivals and sampled generated domain; they do not prove unique induction against every possible rule. Profile identity remains deliberately recoverable from total foreground count, but the output law is independently witnessed in every scene across all overlap arities, and witness positions are shuffled rather than fixed.
## Current reviewer considerations

Source SHA-256: `ee0823fa1e8b2781c8a5425b44a87a7af69d66240a01433881caf02594476c6a`.

# Decisions

## D1 — Preserve the selected Racket authority

- **Input choice:** Keep canonical `program_solution`, selected `target_code`, and `RULE_HASH=d5832237956b` unchanged.
- **Original rationale:** All 7 canonical pairs, 120 rule-smoke calls, and mirror parity already established the intended physical-band overlay. The defect was in teaching distribution, not label authority.
- **Alternatives considered:** Rewrite or simplify the Racket rule; re-pin a behavior-only hash. Both would create unnecessary authority risk.
- **Probe:** Before and final authority-sync/rule-smoke stages; final execution parity is clean.
- **Failure mode/limit:** The archival `raw_code` remains textually divergent but behaviorally equivalent; authority-sync labels this explicitly rather than treating it as selected source.

## D2 — Give every scene overlap arities 0 through 4

- **Input choice:** Reserve ten shuffled projected coordinates: six exact pair roles, one three-way role, one four-way role, one lowest-priority singleton, and one all-zero cell.
- **Original rationale:** The baseline had all pairwise comparisons but no scene contained both three-way and four-way conflicts. Multiplicity-specific rivals could therefore remain untested in a short lesson.
- **Alternatives considered:** Depend on random free-cell occupancy to occasionally create high-order overlaps; add more demonstrations instead of stronger examples. Random coverage is non-contractual, and more examples would alter downstream lesson size.
- **Probe:** Test-first regressions `test_every_generated_scene_covers_all_projected_overlap_arities` and `test_two_step_schedule_refutes_overlap_arity_shortcuts`; semantic gate reports both new witnesses firing 600/600.
- **Failure mode/limit:** Reserved witnesses make each scene intentionally information-dense; positions are shuffled, but the generator is not modeling a natural sparse process.

## D3 — Mix free-cell arities without breaking exact profile observability

- **Input choice:** Around target mean arity 1/2/3, pair free coordinates as `(target-1,target+1)` and leave one target value only when the free count is odd. Shuffle the resulting arity list.
- **Original rationale:** Filling every free coordinate with one arity created a visible profile-wide artifact. Symmetric mixing preserves the exact total foreground count used by `observe_overrides`.
- **Alternatives considered:** Sample independent Bernoulli occupancy and infer profile approximately; add an explicit marker encoding the profile. Both would weaken exact controls or add an irrelevant cue.
- **Probe:** The red distribution regression failed for all three profiles; the repaired test passed. The retained probe sampled 144 unique draws across widths 4, 6, and 12: all covered arities 0–4 and all recovered the requested profile exactly.
- **Failure mode/limit:** Each profile still has a characteristic occupancy distribution (`0/2`, `1/3`, or `2/4`) because profile density is an advertised axis. The output law is nevertheless independently witnessed at every arity in every scene.

## D4 — Declare multiplicity-specific rivals explicitly

- **Input choice:** Add `reverse_on_three_way` and `reverse_on_four_way` to `SEMANTIC_RIVALS`/`LESSON_COMPETITORS`, plus matching witnesses and rival claims.
- **Original rationale:** A teaching contract should name the precise alternatives that motivated the distribution repair; otherwise a clean generic battery can regress silently.
- **Alternatives considered:** Keep only tests around raw multiplicity counts. Counts show presence but not that the labelled output distinguishes the intended rule.
- **Probe:** Initial test failed because the rival names were absent; final semantic gate verifies 11/11 witnesses and 11/11 rival claims.
- **Failure mode/limit:** The rival set is finite and cannot prove unique induction against every possible program.

## D5 — Exclude the unique max-color-aligned varied palette

- **Input choice:** Continue using the canonical color set, but reject both the identity mapping and the one varied tuple `(8,5,2,4)` whose descending numeric order matches physical priority `(0,1,3,2)`.
- **Original rationale:** The first full census found 0 ordinary ambiguities but one rotated ambiguity: two demonstrations with `(8,5,2,4)` allowed `max_color_overlay` to survive and fail on the held-out third sample.
- **Alternatives considered:** Remove `max_color_overlay` from declared rivals; force every lesson to contain a particular palette; increase lesson size. Removing the rival would hide a plausible shortcut, while stronger scheduling or larger lessons were unnecessary once every individual scene could refute it.
- **Probe:** Exact failing lesson retained in `checks/lesson-census.json`; regression `test_same_seed_lesson_remains_identifiable_under_every_query_rotation` failed before and passed after. Final census: 0/900 ambiguous rotations.
- **Failure mode/limit:** One of 23 nonidentity color permutations is no longer sampled. This is a deliberate teaching restriction, not a claim about all lawful inputs.

## D6 — Model the production lesson sampler exactly in local probes

- **Input choice:** Use one lesson seed for all consecutive sample indices, matching the source-bound materializer, and test all small cyclic starts.
- **Original rationale:** The first task-local probe changed seeds between demonstrations and accidentally decorrelated palette choices, masking the max-color failure.
- **Alternatives considered:** Keep independent seeds as a broader diversity probe. That is useful separately but does not validate the actual training assembly.
- **Probe:** `workspace/overlap_arity_probe.py` now records the same-seed policy; final run found 0 ambiguous declared-rival lessons across 48 cyclic windows.
- **Failure mode/limit:** Forty-eight cyclic windows are a deterministic focused check; the separate 300-lesson census supplies larger source-bound coverage.

## D7 — Keep exact controls and canonical support stable

- **Input choice:** Preserve `grid_w`, `mask_profile`, and `palette_mode` as the only public axes; preserve exact total counts for profile recovery and the four-slot schedule.
- **Original rationale:** These controls were already meaningful and passed the baseline. The repair should improve within-axis distributions, not rename or expand the API.
- **Alternatives considered:** Replace `mask_profile` with an unobservable stochastic density parameter; add overlap-arity as another public axis. Both would complicate the contract and allow under-informative scenes.
- **Probe:** Final override gate accepted 5,940/5,940 draws across 66 cases; profile floor retained support in all bands (8/20 easy, 3/20 medium, 5/20 hard).
- **Failure mode/limit:** Exact profile recovery relies on the constructive count formula, so arbitrary externally supplied lawful grids may not map to a generated profile.

## D8 — Build reusable evidence rather than a one-off explanation

- **Input choice:** Retain `workspace/overlap_arity_probe.py`, exact red/green task-test runs, the first ambiguous census, final census, and the Racket-backed shortcut counterexample.
- **Original rationale:** Future edits need a fast way to detect the same distribution and lesson-assembly regressions.
- **Alternatives considered:** Document only the final passing battery. The baseline was already all green, so that would erase the evidence that justified the repair.
- **Probe:** Fresh-packet patch replay and portable task tests are recorded in `RESULTS.json`.
- **Failure mode/limit:** Evidence is source-bound to this packet/tool version; future tooling changes should replay rather than blindly compare report formatting.

## Review `review-9a1946e9f5771cdb` — 2026-10-23

Final generator SHA-256: `773d54bdbec469ca64c9e2037e2a9cf1ef0033aa601e4539c482b0332d7ee4f1` (baseline `ee0823fa1e8b2781c8a5425b44a87a7af69d66240a01433881caf02594476c6a`). Prior accepted return `review-e6563d790feff771:v0001` and audit `review-81a161b804acb61f:v0001` were used only as leads; current-source checks were rerun.

The intended rule remains unchanged: overlay four stacked 3-row masks onto one frame and choose the first occupied band in physical priority `0 > 1 > 3 > 2`. The selected/canonical Racket authority and `RULE_HASH=d5832237956b` did not change, and lawful generation/distribution did not change.

### Current repair

The strict defect lint found 33 public-call scalar violations: `generate()`/`schedule_profile()` accepted boolean, float, and string lookalikes, and negative `sample_index`, because the schedule path coerced with `int(...)` and the public boundary did not validate. Both entry points now require exact Python integers and reject negative sample indices before scheduling or RNG construction. Negative integer seeds remain valid and deterministic. The minimal source-bound record is `counterexamples/strict-call-scalars.json`; focused tests are in `tests/test_public_scalars.py`.

Final evidence: 12/12 battery stages green; 55/55 portable selected-task tests; 300 production lessons (100 per band), 900 unique inputs, 0 production ambiguity, 0/900 ambiguous query rotations, and no hook/scoring/materialization errors against declared rivals. A seed-17 production request emitted 3 automatic demonstrations + 4 distinct queries with seven Racket labels and all declared rivals refuted for every query. These are finite declared-rival checks, not universal identifiability.

### Proposed parameter extension

`workspace/parametric/` contains a separate, unapproved `lower_band_order` prototype. The canonical setting keeps `0 > 1 > 3 > 2`; the alternative changes only the lower comparison to `0 > 1 > 2 > 3`. Inputs preserve the original four-mask projection and are independent of the hidden setting. Each retained setting has 2 demonstrations + 4 distinct queries; verification replayed 19 Racket labels with zero paired-setting query ambiguity. The canonical setting is byte-for-byte authority-identical. This prototype does not alter production, catalog approval, or training admission.

### Open limits

The task-local scalar validator should eventually be replaced by a shared public-call contract to prevent repeated fixes. The parameter alternative still needs independent rule, difficulty, and admission review. No Qwen3.5-9B training experiment was run.


## Current external prototype follow-up

The prototype has independent demo_count/query_count controls (reported2demos+4queries per setting), whitelisted public bytes and visible-content hash filenames. materialize nevertheless writes public files immediately in seed,seed+1 order rather than sorted visible-content order; default seed parity maps that creation order to hidden settings. Preserve reported19Racket replays; the remaining ask is a narrow sorted-batch writer/privacy regression. The exact reviewer program remains unchanged and unapproved. External work must use visible-content public identifiers and independent demo/query counts, then exercise four queries through Racket with focused privacy/count checks. Source-bound pending work: `generators/3a0af56db83e/evidence/parametric-external-followup-9a1946e9f5771cdb/manifest.json`. Owner inspection was static; reported batteries were not rerun.

## 2026-10-23 external prototype privacy repair (`review-8ee1ad2cb366f70d`)

The retained follow-up was reproduced: public filenames were derived only from visible challenge bytes, but `materialize()` wrote the two public files in `seed, seed+1` order. Because seed parity selects the hidden `lower_band_order`, inode/directory creation order exposed the private setting schedule even though names and contents were clean.

The prototype now builds both public artifacts in memory and writes them sorted by their visible-content filename. Private episode records remain in episode order. A test-first regression spies on the real writer and failed on the old seed-0 order (`6ff…` before `1e…`) before passing with the sorted batch. The production generator and canonical authority remain unchanged: generator SHA-256 `773d54bdbec469ca64c9e2037e2a9cf1ef0033aa601e4539c482b0332d7ee4f1`, `RULE_HASH=d5832237956b`. Prototype SHA-256 is now `d336daacb4f2fc3093ae56e4734cee91e716a0d0e74b92bb653d6c3d2d9b383b`.

Fresh evidence replayed 7 canonical labels and 12 episode labels through Racket for 2 settings, 4 demonstrations, and 8 queries with zero declared-setting ambiguities. The focused parametric suite is 18/18 green, and the packet's source-bound `task_tests` wrapper is 57/57 green. A bounded adversarial probe checked seeds 0–3, confirmed visible-name write ordering and public-field privacy, rejected a forced duplicate visible ID before public emission, and showed that a one-cell public-label tamper is rejected by the verifier. Raw direct collection of the whole task test directory is still unavailable in this packet because two unchanged production modules import the omitted generated `puzzle_generators.per_puzzle` package; the source-bound wrapper is the supported receipt.

The prototype remains unapproved and outside production/training admission. A useful promotion-time follow-up is to switch the local filename helper to the shared public-challenge helper so the prototype and shared writer use one canonical byte/ID implementation.
