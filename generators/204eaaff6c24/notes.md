# Working notes: 204eaaff6c24

## Current account

- **Selected rule:** on a 0-background grid with exactly one nonzero color, count all nonzero cells `N` and output a horizontal `1 × N` bar in that color. `RULE_HASH=4571597a8055`; canonical semantics are unchanged.
- **Current generator:** version `3.0.0`, SHA-256 `8aec638b293e27e7d1e9a8b71aca5e3b089b4813f7d7f4e2b377080364ad4985` at final verification.
- **Domain:** dimensions 3..12, colors 1..9, count 1..30, at least one background cell; connectedness and shape are intentionally unconstrained.
- **Exact controls:** strict `grid_h`, `grid_w`, `fg_color`, `n_cells`, and one of `fg_layout`/`texture`. Unknown keys, scalar coercions, alias conflicts, and infeasible exact combinations reject; joint conflicts expose `incompatible_axes`.
- **Teaching policy:** deterministic four-profile schedule with two disconnected witnesses. Declared rival: count only the largest 8-connected foreground component.
- **Measured support:** strict canonical profile 21/60 overall (easy 10/20, medium 5/20, hard 6/20); 300 four-demo/one-query lessons and all 1,500 query rotations had no ambiguity against the declared rival; fixed-seed four-start census passed 12 lessons/60 rotations.
- **Authority:** selected base `racket_target.target_code` synchronized to exact canonical program bytes; archival `raw_code` left unchanged; execution parity passes.
- **Open finding:** strict shared defect lint still warns because singleton, short line, solid 2×2, and many topology mutations are lawful for this count-only rule. Do not narrow `self_check` merely to silence it. Source-bound evidence: `checks/lawful-minimal-probe.json`.
- **Current parametric deliverable:** native `count_mode={all_cells,anchor_indexed_component}` family under `workspace/parametric/`; `all_cells` preserves the exact canonical program while the alternate uses an input-derived anchor-component size to select and count another component. Native qualification is reviewer-passed; owner acceptance remains pending.

## 2026-10-25 native parametric family

The prior horizontal/vertical output-orientation prototype was superseded in the active native contract because its dependency was cosmetic; its legacy baseline source and test remain unchanged for return-delta compatibility. The replacement keeps `all_cells` as the byte-exact canonical default and adds `anchor_indexed_component`: segment the sole foreground color into row-major 4-connected components, measure the first component size `k`, select remaining component `(k-1) mod m`, count it, and emit a same-color horizontal bar. The selected target and output length cannot be known before measuring `k`.

The family supports 2–6 demonstrations and 1–4 prefix-stable queries with matched visible inputs. Its fourth query is a lawful 30×30 case with exactly 30 foreground cells. The finite teaching audit covered 20 episodes, 12 declared rivals, 44 protected-Racket evaluations, and found no surviving rival or label mismatch. Native qualification passed both settings at seeds 0 and 17 (4 jobs, 40 protected-Racket labels). A source-bound wrong-intermediate witness changes `k` to `k+1`, selecting a different component and changing the final output. Public projection produced 16 validated one-query views.

Limits: the rival inventory is finite, reviewer `ready` is not owner acceptance, and no training admission was performed. Current evidence is under `workspace/parametric/evidence/` and `checks/204eaaff6c24/`.

## Reversed decisions

1. **Permissive override coercion → strict validation.** Prior unknown axes and float/bool/string coercions made exact requests unverifiable. Final override stage passes with 0 findings.
2. **Area-first free dimensions → layout-aware joint construction.** Prior band-sized canvases could reject feasible exact row/column/diagonal counts. Free axes now grow conditionally inside the declared envelope; explicit axes remain exact.
3. **Stochastic witness occurrence → deterministic four-profile teaching schedule.** The canonical-fitting largest-component shortcut required guaranteed refutation in every four-pair lesson and every three-of-four rotation.

Imported associated notes and unresolved historical reports remain in `evidence/`; they were used as leads, not as proof of the final source. Detailed rationale and alternatives are in the return-root `DECISIONS.md`.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-759eeb311521ba5d:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `8aec638b293e27e7d1e9a8b71aca5e3b089b4813f7d7f4e2b377080364ad4985`. At disposition, audited bytes match the current source.

### Current decision

Source prose means `repo/generators/204eaaff6c24/generator.py`. Reviewer-reported on unchanged source 8aec638b293e27e7d1e9a8b71aca5e3b089b4813f7d7f4e2b377080364ad4985. No issue in bounded canonical/schedule/rival audit:5 canonical pairs,12 deterministic4-pair lesson windows covering4 starts in3 bands,20 unique generated inputs,60 single-query rotations; declared largest_8_connected_component rival never survives demos then differs on query.41 portable task tests reported passed. This does not establish universal approval or cover undeclared rivals. Exact target-local evidence: `checks/audit/204eaaff6c24-task-tests/RUNTIME_MANIFEST.json` `checks/audit/204eaaff6c24-task-tests/checks/task_tests.xml` `checks/audit/204eaaff6c24-task-tests/progress.log` `checks/audit/204eaaff6c24-task-tests/result.json` `checks/audit/204eaaff6c24/schedule-probe.json`

### Assessment or prior finding

## 204eaaff6c24

**No issue found in the bounded schedule/rival audit.** On generator SHA `8aec638b293e27e7d1e9a8b71aca5e3b089b4813f7d7f4e2b377080364ad4985`, I checked all 5 canonical pairs and 12 deterministic four-pair lesson windows: four cyclic starts in each of easy, medium, and hard. Across 20 unique generated inputs and all 60 single-query rotations, the declared `largest_8_connected_component` rival never survived the demonstrations while differing on the query; there were zero failures. The source-bound materialized windows and outputs are in `checks/audit/204eaaff6c24/schedule-probe.json`.

The target's portable task tests also passed 41/41 in 12.98 seconds (`checks/audit/204eaaff6c24-task-tests/result.json`). This is a clean result only for the checked canonical labels, four-profile schedule, and declared largest-component rival; it is not universal approval or proof against undeclared hypotheses. I left the audit target unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `8aec638b293e27e7d1e9a8b71aca5e3b089b4813f7d7f4e2b377080364ad4985`.

# Decisions: 204eaaff6c24

## D1 — Preserve the canonical rule

**Prior choice:** count every cell of the sole nonzero color and emit a horizontal `1 × N` bar.
**Current choice:** unchanged; `RULE_HASH` remains `4571597a8055`.
**Reason:** all five canonical pairs, the independent count oracle, rule smoke, and the post-repair visible solve agree. No evidence justified changing semantics.
**Alternative rejected:** encode connected components, shape class, or layout in the output. Those alternatives contradict lawful canonical-domain inputs and would only silence generic lint.
**Evidence/limit:** `checks/after-final/checks/204eaaff6c24_after_rule_smoke.json`; finite checks do not prove the canonical interpretation against every possible hypothesis.

## D2 — Strictly validate public call scalars and override axes

**Prior choice:** keyed draw calls received unvalidated values, permitting Python coercion (`2.7 → 2`, `True → 1`, numeric strings) and silently ignored unknown keys.
**Current choice:** validate exact Python types and ranges before drawing; reject unknown axes; reject simultaneous `fg_layout` and `texture`; attach sorted `incompatible_axes` to joint-feasibility `ValueError`s.
**Reason:** typo/coercion acceptance makes requested curricula unreproducible and downstream evidence cannot tell requested values from accidental casts.
**Alternatives considered:** retain permissive compatibility, warn only, or coerce strings. Rejected because the task advertises exact axes and the strict override checker expects observable or explicitly incompatible controls.
**Probe:** failing-first coverage in `checks/tdd-red.log`; final cases in `tests/test_generator.py`; `checks/after-final/checks/204eaaff6c24_after_override_results.json`.
**Limit:** `observe_overrides` reports semantic color/count only; layout and dimensions remain directly observable from the grid rather than duplicated in the hook.

## D3 — Select dimensions jointly with count and layout

**Prior choice:** free dimensions grew for total area before the selected layout capacity was known, so feasible diagonal/row/column requests could be rejected.
**Current choice:** enumerate feasible dimension pairs, draw height only from values retaining a feasible width, then draw width conditionally. Explicit axes remain exact; free axes may grow only within 3..12.
**Reason:** a request such as `n_cells=8, fg_layout="diagonal"` is feasible in the declared envelope and should not fail merely because a smaller band-default canvas was sampled first.
**Alternatives considered:** always force square canvases; silently change explicit dimensions; retry randomly. Rejected respectively for distribution narrowing, contract violation, and nondeterministic failure.
**Probe:** `test_free_dimensions_grow_to_honor_large_layout_specific_count`; structured-conflict tests for genuinely impossible explicit combinations.
**Limit:** exact counts still require one background cell; impossible requests reject rather than weakening that domain invariant.

## D4 — Retain broad count, color, and layout support

**Count:** preserve `1..30`; use band defaults of 1..8 easy, 1..15 medium, 5..30 hard, with scheduled canonical witnesses in 2..4.
**Color:** preserve all foreground colors 1..9, excluding only background 0.
**Layout:** preserve random, cluster, row, column, diagonal, blob, and scattered.
**Reason:** the rule is independent of topology, size profile, and color identity; narrowing any of these would encourage shortcuts.
**Alternatives rejected:** remove singleton/line/solid shapes or require disconnectedness globally. Both falsify the intended count-only domain.
**Evidence:** strict profile floor `checks/after-final/checks/204eaaff6c24_after_profile_floor.json`, distribution gate, 600-draw semantic report, and `checks/lawful-minimal-probe.json`.
**Limit:** the declared 3..12 input envelope and 30-cell cap are engineering bounds, not semantic necessities.

## D5 — Replace stochastic teaching luck with a four-profile schedule

**Prior choice:** default draws could form lessons in which every foreground was one 8-connected component, leaving “count only the largest component” observationally equivalent.
**Current choice:** declare `LESSON_SCHEDULE_PERIOD = 4` with two ordinary profiles and two disconnected witness profiles, one of which exactly matches the canonical 3×3/two-color-profile shape statistics.
**Reason:** the rival fits all canonical demonstrations, so generated lessons must actively distinguish it rather than rely on random occurrence.
**Alternatives considered:** force every pair disconnected; add more demonstrations; resample whole lessons until a witness appears. The first narrows distribution, the second changes the requested lesson size, and the third complicates reproducibility.
**Evidence:** exact counterexample under `counterexamples/review-1a6689fc7652152c/`; 300-lesson census and complete four-start receipt.
**Limit:** the contract covers the declared largest-component rival and finite generic rivals, not all possible schedule-aware rules.

## D6 — Keep self-check semantic, not topology-specific

**Prior/current principle:** `self_check` should enforce dimensions, ARC colors, one nonzero color, count/output length, and at least one background cell—nothing about connectedness or shape.
**Decision:** retain lawful singleton, short-line, solid-2×2, connected, and disconnected inputs even though generic defect lint warns.
**Reason:** the exact Racket rule uses only nonzero color and count; topology rejection would reject valid inputs and make the generator semantically narrower than its authority.
**Probe:** `workspace/lawful_minimal_probe.py` plus `tests/test_lawful_minimal_probe.py`; final evidence `checks/lawful-minimal-probe.json`.
**Limit:** the probe checks only three named controls and is not a blanket exemption.

## D7 — Synchronize only selected active authority text

**Prior choice:** selected base `racket_target.target_code` was textually divergent from canonical authority while execution parity passed; archival `raw_code` was also divergent.
**Current choice:** update only `/racket_target/target_code` to exact canonical bytes. Preserve archival `raw_code` unchanged.
**Reason:** selected execution authority should be byte-bound and auditable; archival provenance should not be rewritten.
**Evidence:** `checks/authority-sync-proposal.json`, `checks/authority-sync-apply.log`, and final authority stage.
**Limit:** this is a synchronization change, not a canonical-rule change; archival divergence remains intentionally reported.

## D8 — Prototype output orientation, but do not select it

**Parameter:** `output_orientation`, chosen once per episode, values `horizontal` (canonical/default) and `vertical` (proposed).
**Reason suitable:** both variants preserve object roles and the core “identify sole color, count all cells” reasoning; only output orientation changes. Inputs use `N ≥ 2` so demonstrations can reveal the setting.
**Evidence:** exact Racket programs and two complete episodes in `checks/parametric/output-orientation-900/`; report status PASS, 2/2 lesson identification and 2/2 query separation.
**Alternatives considered:** output color remapping or count transformation. Rejected because they alter more of the original semantic structure and invite arbitrary parameterization.
**Decision:** keep the extension isolated under `workspace/parametric/`; do not change production, authority, approval, or default generation.
**Limits:** only two values, two evidence episodes, and the opposite setting as the named rival; `N=1` cannot distinguish orientation.

## D9 — Report completion as blocked rather than falsify the domain

**Choice:** retain the final battery’s one failed strict stage and mark completion `blocked`.
**Reason:** both warning classes arise from a shared generic heuristic. A task-local “fix” would have to reject Racket-lawful inputs or invent a topology invariant.
**Suggested integration decision:** accept the generator repair with an explicit warning disposition, or add the source-bound exemption mechanism proposed in `FEEDBACK_TO_CODEX.md` F1.
**Evidence:** `checks/after-final/checks/204eaaff6c24_after_defect_lint.log` and `checks/lawful-minimal-probe.json`.
