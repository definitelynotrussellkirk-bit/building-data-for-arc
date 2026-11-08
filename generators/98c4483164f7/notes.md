# Working notes: 98c4483164f7

## Current parametric extension — proposed

The canonical generator and reference rule remain version 2.0.0 / `18ad2f5cfd8b` at source `34e2b872a68979a620411d5ea434100d2489073e19bc74fe4e72602945603a78`. The new independent authoring code is in `workspace/parametric/`.

Chosen rule controls are `quarter_turns ∈ {0,1,2,3}` clockwise and `stride ∈ {1,2}`. Default `(0,1)` is the exact canonical Racket text. Object roles, quadrant selection, payload recoloring, all-four-cell origins, and boundary clipping stay invariant; projection direction and spacing change. Pure size/position controls were insufficient because they would not change the transformation.

The adapter fixes parameters once per episode, supports 3..8 demonstrations independently of 1..8 queries, uses a bounded 256-attempt distinct sampler, and includes a meaningful 6..30 shape schedule. The certificate fits eight settings and 40 shortcut variants on demonstrations only; the protected Racket worker independently checks all eight settings and chosen labels. Public hashes depend only on the exact visible bytes.

The production repair (`review-642b00005c62a3c2:v0001`) and the later parametric return (`review-19e7793312ed1cfa:v0001`) are compatible in the current tree: the approved generator and canonical rule remain byte-identical, while the prototype stays isolated under `workspace/parametric/`. The task-local evidence manifest already binds `adapter.py`, `promotion.json`, their resources, tests, and retained evidence; the earlier handoff sentence saying that inventory update was still pending is superseded.

Current retained evidence: the original prototype matrix contains 16 episodes at seeds 0 and 17, each with 3 demonstrations and 4 distinct queries, including 6×6, 30×30, 6×30, and 30×6 queries; 448 protected Racket evaluations and 112 saved-label replay evaluations passed. Reconciliation checks repeated the owner qualification path on all eight settings at both 3-demo/4-query and maximum 8-demo/8-query limits (448 and 1,152 protected Racket evaluations), and independently matched Python against Racket on 408 lawful 2×2/edge/thin-grid cases outside production sampling. Focused task tests remain 87 passed with 67 subtests. See `workspace/reconciliation/conflict-reconciliation-20261023.json`.

Next owner action: review the parameter semantics and, only if satisfied, run the explicit acceptance command against a fresh qualification receipt. Inventory binding and qualification readiness are no longer blockers. The prototype is still proposed; no variant acceptance or training admission follows from this reconciliation. See the prototype README for the finite-rival limits.

## Current rule and scope

A filled nonzero 2×2 motif sits on a literal color-0 background. Red (`2`) cells mark active diagonal quadrants. The other nonzero color is the payload: recolor all four motif cells to it, then project that color from all four motif cells to the boundary in every active diagonal direction.

Version `2.0.0`; canonical rule hash `18ad2f5cfd8b`.

## 2026-10-08 review repair

The prior v1.2.0 source advertised copied/inert axes (`palette_kind`, `anchor_corner`, `asymmetry_force`, singleton palette controls, and texture degenerates), silently accepted unknown keys, omitted `RULE_HASH`, and had no executable semantic/lesson contract. A baseline override run produced 6,477 findings. `anchor_corner=True` was specifically accepted but ignored.

The repair reverses that choice. The public surface is now only four exact, observable axes: `grid_h` 6..30, `grid_w` 6..30, `n_red_cells` 1..3, and `main_color` in `{1,3,4,5,6,7,8,9}`. Unknown, retired, mistyped, and out-of-range controls are rejected. Generated motifs retain two cells of clearance; corner anchoring was retired because it truncates the rays that the lesson must reveal.

## Curriculum

Default marker profiles cycle deterministically:

1. one marker;
2. opposite pair;
3. three markers;
4. adjacent pair.

`EXAMPLES_NEEDED = 3`. Every third sample independently uses canonical 9×9 geometry. The first attempt used period four for both semantics and geometry and measured 14/60 = 23.3% canonical-profile support; decoupling geometry to period three measured 24/60 = 40% while preserving the 1–2–3–2 lesson cycle.

Six declared rivals/witnesses cover no projection, all quadrants, red-only origins, opposite quadrants, first-marker-only, and one-step rays. `lesson_identifiable` validates labels and rejects a three-demo lesson if any named rival survives.

## Verification

- Final generator SHA-256: `34e2b872a68979a620411d5ea434100d2489073e19bc74fe4e72602945603a78`.
- Full after battery: 12/12 green.
- Portable task tests: 62 passed.
- Override contract: 8,100/8,100 draws, zero findings, unknown key rejected.
- Semantic smoke: 12/12 lessons, 0/48 ambiguous rotations.
- Large census: 300/300 lessons, 0/1,200 ambiguous rotations, 1,141 unique inputs.

The selected task-specific base Racket copy was synchronized exactly to the unchanged canonical authority; execution parity passes.

## Known limits

The generator intentionally covers one 2×2 motif on a zero background and does not claim every legal edge placement. `self_check` still accepts canonical lawful inputs without the production clearance restriction. The semantic results are finite declared-rival evidence, not proof against all hypotheses. The large census rotates sampled bundles but does not enumerate every possible schedule start.

## Current reviewer considerations

Source SHA-256: `34e2b872a68979a620411d5ea434100d2489073e19bc74fe4e72602945603a78`.

# Decisions for `98c4483164f7`

## D1 — Preserve the canonical rule; synchronize the selected authority copy

**Prior state.** The selected base record contained an older executable spelling that was behaviorally related but textually divergent from the canonical `program_solution`. This made authority synchronization fail after the generator repair.

**Decision.** Keep the canonical rule unchanged and copy its exact source into both `racket_target.raw_code` and `racket_target.target_code` in `repo/shared/data/base/solutions/training/1f0c79e5__98c4483164f7.json`; mark it `synced_to_canonical_authority`.

**Evidence.** `checks/after-final/checks/98c4483164f7_after_authority_sync.json` reports `synchronized` and execution parity `PASS`. The canonical ledger was not edited.

## D2 — Replace copied metadata with four exact controls

**Prior state.** Version 1.2.0 advertised copied axes (`palette_kind`, `anchor_corner`, `asymmetry_force`, `palette_size`, `position_bias`, `n_distinct_colors`, `texture`) that were inert, singleton, aliased, or unlawful. Unknown keys were accepted. The baseline override gate produced **6,477 findings** over 24,210 draws, including 4,860 `self_check` findings and 1,080 override mismatches (`checks/before-targeted/override/...before_override_results.json`).

**Decision.** Advertise only `grid_h`, `grid_w`, `n_red_cells`, and `main_color`; make each exact and observable; reject unknown, retired, mistyped, and out-of-range values.

**Rejected alternative.** Retaining `anchor_corner` as a real axis would force truncated/zero-length rays at the border and weaken the lesson. Retaining “degenerate textures” would emit inputs outside the task grammar.

**Evidence.** The final override matrix accepted **8,100/8,100 draws**, covering 90 cases × 3 bands, with zero findings/warnings and unknown-key rejection: `checks/after-final/checks/98c4483164f7_after_override_results.json`.

## D3 — Require two cells of clearance

**Decision.** Generated motifs are placed with two background cells on every side; exact dimensions therefore begin at 6×6. This guarantees that selected rays visibly continue beyond the motif and that inactive quadrants remain observable.

**Failure mode avoided.** Corner/edge motifs can make distinct hypotheses (`no_rays`, `one_step_rays`, opposite direction) answer identically because a ray immediately exits the canvas.

**Limit.** `self_check` accepts lawful canonical motifs without this stronger clearance; the restriction applies to production generation, not to the task rule.

## D4 — Use a deterministic four-step semantic schedule

**Decision.** Cycle marker relations as `single_marker`, `opposite_pair`, `triple`, `adjacent_pair`, giving red counts `1,2,3,2`. Three consecutive demonstrations are the declared lesson minimum.

**Rejected alternative.** IID marker masks can produce three single-marker demonstrations or omit multi-marker union behavior. A full enumeration per lesson would be stronger but needlessly expands every lesson.

**Evidence.** Focused tests enumerate sliding three-demo windows and all named competitors. The semantic battery materialized 12 lessons with 3 demonstrations each and found 12/12 identifiable; 48/48 held-out query rotations were unambiguous: `checks/after-final/checks/98c4483164f7_after_semantic_gate.json`.

## D5 — Decouple canonical geometry from the four-step lesson period

**Initial repair.** Canonical 9×9 geometry was tied to the period-four marker schedule. Under the pinned profile sampler this produced only **14/60 = 23.3%** exact canonical-profile hits, below the declared 25% floor (`checks/after-targeted/profile_floor/...profile_floor.json`).

**Final decision.** Use an independent period-three 9×9 anchor while retaining the period-four semantic schedule.

**Evidence.** The rerun produced **24/60 = 40%** exact hits, with support in every band (`checks/after-final/checks/98c4483164f7_after_profile_floor.json`). This is a measured sampler fix, not a rule change.

## D6 — Make semantic claims executable

**Decision.** Add an independent Python mirror plus six named rivals and witnesses: no rays, all directions, red origins only, opposite directions, first marker only, and one-step rays. `lesson_identifiable` validates every label and rejects any lesson whose three demos leave a named rival alive.

**Evidence.** The semantic gate observed 600/600 lawful draws, 192 strict-profile hits (32% ≥ 25%), all six witness/rival contracts, 12/12 identifiable lessons, and 0/48 ambiguous rotations. The larger source-bound census materialized **300/300 lessons**, scored **1,200 pairs and 1,200 rotations**, found zero ambiguity/errors, and retained **1,141 unique inputs** in `checks/lesson-census-final.json`.

**Limit.** These are finite declared-rival checks, not proof of unique induction against every possible rule. The census rotates pairs within sampled bundles; it does not enumerate every possible schedule start.

## D7 — Add portable, source-bound regressions

**Decision.** Add 62 focused tests under the selected task, using `reviewer_support.find_root` and canonical helpers rather than fixed parent-depth assumptions. Tests cover canonical parity, exact controls, retired-key rejection, deterministic schedule support, witness firing, all sliding windows, and malformed-grid diagnostics.

**Evidence.** Portable task snapshot: **62 passed, 0 failed** in `checks/task-tests-final2/result.json`.

## D8 — Stop after a fresh visible-example solve

The post-repair solver inferred the 2×2 marker/ray transformation and passed 3/3 visible demonstrations in one revision. Earlier rule exposure was disclosed as `yes`; no reference or private labels were consulted during the solve episode. The private query result remains intentionally unknown.
