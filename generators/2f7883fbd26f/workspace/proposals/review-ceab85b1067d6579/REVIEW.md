# Review — `2f7883fbd26f`
Task/version: final generator SHA `2b1bfbcfb59638475bc152c8792ba04672d8b400f1689fc78176314f1369c353`, version `2.0.0`.
Baseline defect: `defect_lint` found 177 accepted invalid scalars; the other 11 battery stages were green.
Repair: exact-type replay-key validation plus `draw_int_strict` for all six declared integer axes.
Legal behavior: unchanged; version/RNG identity stayed `2.0.0`, and the retained seed-4242 witness reproduced byte-for-byte.
Canonical rule/Racket authority: unchanged; `RULE_HASH = 6de5b0b7a0a5` remains synchronized.
Parametric result: proposed separate `(window_size, target_color)` prototype; 4 settings, 4 complete episodes, 68 protected-Racket applications.
Final battery: 12/12 stages green at the final generator hash.
Portable task tests: 18/18 passed, including strict-scalar and parametric regressions.
Lesson evidence: 2 ordered demonstrations; 300/300 production lessons and 900/900 held-out rotations had no ambiguity against both declared rivals.
Cyclic schedule probe: 450/450 windows and 1,350/1,350 rotations contained/refuted the required overlap rivals.
Fresh final-source solve: 3/3 visible demonstrations passed; earlier exposure declared `yes`, reference consulted `no`.
Remaining limitations: finite named-rival/controlled-fixture evidence only; two audit targets have findings and were intentionally left unchanged. Acceptance: routine for the selected repair.

## What changed

### S1 — Reject coercible scalar controls

The baseline generator routed declared integer overrides through `GenCtx.draw_int`, which calls `int(value)`. It therefore accepted booleans, numeric strings, integral floats, and fractional floats; `seed` and `sample_index` likewise lacked exact-type validation, and negative sample indices were accepted. The completed baseline battery records 177 `strict-scalar` findings in `checks/before/checks/2f7883fbd26f_before_defect_lint.log`.

The repair adds one replay-identity validator, calls it before scheduling/RNG construction, rejects negative sample indices, and routes declared integer overrides through the existing `draw_int_strict` primitive. No valid range, sampling weight, schedule role, rule text, or generator version changed. Minimal evidence is retained in `repo/generators/2f7883fbd26f/counterexamples/strict-scalars/counterexample.json`; focused regressions are in `repo/generators/2f7883fbd26f/tests/test_strict_scalars.py`.

### P1 — Build, but do not integrate, a small parametric family

`repo/generators/2f7883fbd26f/workspace/parametric/prototype.py` instantiates two episode-level parameters:

- `window_size ∈ {2, 3}`, canonical default `2`;
- `target_color ∈ {1, 2}`, canonical default `1`.

The default rule text is byte-for-byte the canonical Racket program. Each complete episode has three labelled demonstrations and one masked query, with the chosen setting fixed across the episode. Controlled 11×13 inputs make all four settings produce distinct signatures; every alternative setting is refuted by the demonstrations. `checks/parametric/window-rule/report.json` records 4 complete episodes, 68 protected-Racket rule applications, exact default-program identity, and no Python-authored labels. This remains a proposed authoring prototype, not a production API or approval.

### Q1 — Preserve the decisive shortcut witness

The strongest canonical-fitting rival counts qualifying color-1 connected components rather than every sliding 2×2 all-1 window. A generated 2×3 all-1 strip has two intended windows but one qualifying component. The final source reproduced the retained seed-4242 input exactly, and live Racket execution returned `[[1,1,0,0,0]]`; evidence is in `checks/question-shortcut-final/racket.json` and `repo/generators/2f7883fbd26f/counterexamples/current-shortcut/`.

## Findings and status

| ID | Affected path/task | Reproducer or evidence | Patch status | Final result |
| --- | --- | --- | --- | --- |
| S1 | `generators/2f7883fbd26f/generator.py` | `checks/before/checks/2f7883fbd26f_before_defect_lint.log`; `counterexamples/strict-scalars/counterexample.json` | Fixed | defect lint green; 18/18 tests |
| P1 | `workspace/parametric/` | `checks/parametric/window-rule/report.json` | Proposed, intentionally separate | 4/4 settings distinguished; 68 Racket applications |
| Q1 | canonical-fitting object-count shortcut | `checks/question-shortcut-final/racket.json` | Existing production witness retained/rebound | final generator emits decisive overlaps |
| A-F2E-OVERRIDE-NKEYS | audit target `f2e717c7c250` | `checks/audit/f2e717c7c250/override-nkeys1-counterexample.json` | Audit only; source untouched | reproduced on 5/5 generated pairs |
| A-459-SHAPE-CONTRACT | audit target `45944a8b8fe1` | `checks/audit/45944a8b8fe1/declared-shape-counterexample.json` | Audit only; source untouched | reproduced on 4/4 generated pairs |

## Verification summary

- Baseline: `checks/before/checks/2f7883fbd26f_before_battery_summary.json` — 11 green, 1 failed (`defect_lint`).
- Final battery: `checks/final-battery/checks/2f7883fbd26f_after_battery_summary.json` — 12 green, no advisory/failure/interruption.
- Portable tests: `checks/final-task-tests/checks/task_tests.xml` — 18 passed.
- Random production/rotation census: `checks/lesson-census-final.summary.json` — 300 materialized lessons, 900 unique inputs, 0 production ambiguities, 0/900 ambiguous rotations.
- Exhaustive declared-cycle probe: `checks/lesson-window-probe-final.json` — 450 windows and 1,350 rotations passed across all three difficulty bands, all three starts, and 50 seeds per start.
- Final solve: `solve/summary.json` — final generator hash bound, one revision, 3/3 visible demonstrations.

The retained 2026-10-04 notes and shortcut evidence were used only as leads. Every current pass/failure claim above was remeasured against this packet’s pinned baseline or final source.
