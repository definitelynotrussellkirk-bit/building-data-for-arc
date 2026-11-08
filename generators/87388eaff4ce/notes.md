# Working notes: 87388eaff4ce

## Intended rule

Treat each nonzero 4-connected component as one object. Crop each object to its bounding box, sort by bounding-box height descending and then by color ascending, and stack the crops top-to-bottom with one all-zero row between them. Crops are left-aligned and the output width is the maximum crop width. The selected canonical Racket authority is unchanged and is pinned by `RULE_HASH = "c701ff882260"`.

## Repaired distribution

The imported `2.0.1` sampler chose distinct object heights on ordinary draws, so the output-relevant equal-height color tie-break had 0/1,000 ordinary support in retained prior audit `review-4bbe40f8398aea03:v0001` (source SHA-256 `d647cb3328bcba6ba33294c77d09a3e55e2fa1cefc9ac8768a019a64c48d676f`). It also exposed dead/degenerate controls, omitted `RULE_HASH`, and had an acceptance-only `self_check`.

Version `3.0.0` replaces that distribution with two exact canonical profiles, `9×12` and `10×13`, each containing exactly three separated objects. Every ordinary draw now contains:

- an equal-height pair whose row-major order opposes color order;
- a taller object with fewer occupied cells than a shorter object;
- a taller object narrower than a shorter object; and
- at least two distinct heights.

Only `grid_h` and `grid_w` remain as exact observable axes. Calls, scalar types, unknown/retired axes, malformed grids, unsupported shape families, destructive mutations, and placement failures are handled explicitly. Placement uses randomized exhaustive backtracking rather than a silent capped retry loop.

## Evidence and decisions

- Final selected generator SHA-256: `d4689258ca72838e9caaff746eb5fef2064103ac92f1946c0630365d9a41a1a7`.
- `counterexamples/teaching-witness-v1/` is the retained minimal input that refutes all four declared competitors.
- `workspace/verify_height_lesson.py` checks canonical compatibility, ordinary lesson witnesses, declared rivals, and optional canonical Racket parity; retained result: `checks/height-lesson/verification.json`.
- The 300-lesson production census (`3` demonstrations plus `1` query per lesson, 100 lessons per band) materialized 1,200 unique inputs and found 0 production ambiguities and 0 ambiguities across all 1,200 query rotations against the four declared competitors. This is finite evidence, not a proof against undeclared rules.
- A separate proposed prototype under `workspace/parametric/` varies only the equal-height tie-break (`color_asc` versus `color_desc`) once per complete episode. Every retained demonstration distinguishes the setting and all 8 retained pairs match their own Racket program. It is not selected by the catalog.

## Known limits

The selected sampler intentionally occupies a narrow canonical envelope and a small audited shape-family vocabulary. It teaches one operation with three objects; it does not cover every reference-lawful object count, shape, grid dimension, or possible rival. The semantic claims are limited to the declared competitors and sampled schedules. Multi-rule interaction, sequential state, contextual gating, and task-defined symbols are not applicable to this single-operation task.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-4bbe40f8398aea03:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `d647cb3328bcba6ba33294c77d09a3e55e2fa1cefc9ac8768a019a64c48d676f`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit source-bound closure against acceptedd4689258ca72838e9caaff746eb5fef2064103ac92f1946c0630365d9a41a1a7: every normal draw now has an equal-height pair whose row-major order conflicts with color-ascending order. Task-owned teaching-witness-v1, tests/test_generator.py, checks/height-lesson/verification.json and final semantic/census evidence report56 tests,120 actual Racket applications and300 lessons/1200 rotations refuting four rivals. Prior zero equal-height ordinary support and weak validation are addressed by exact structural profiles and57/57 destructive mutation rejections. Reviewer-reported finite evidence; narrow two-profile/three-object support and undeclared rivals remain limits.

### Assessment or prior finding

## 87388eaff4ce

**Classification: reproduced teaching-coverage defect.**

The authority sorts object crops by bounding-box height descending and breaks
equal-height ties by color ascending. The ordinary sampler deliberately chooses
distinct heights, so normal training examples never exercise the color tie-break.
In the retained 1,000-sample census (sample indices 0–999, seed formula
`873000 + sample_index`, cycling easy/medium/hard), **0/1,000** samples contained
equal bounding-box heights; all 1,000 passed `self_check`. Component counts were
524 two-object, 298 three-object, and 178 four-object samples. Evidence:
`checks/audit/87388eaff4ce/distribution_probe.json`.

The advertised override `texture=all_same_height` provides a minimized legal
counterexample. It was generated with seed 0, sample index 0, passes the target's
`self_check`, and belongs to the documented degenerate generator domain. All
three objects have height two and colors 4, 6, and 7. The Racket authority emits
them in color-ascending order `(4, 6, 7)`, while the rival
`height_desc_then_color_desc_on_ties` emits `(7, 6, 4)`.

- Drawn generator SHA-256:
  `d647cb3328bcba6ba33294c77d09a3e55e2fa1cefc9ac8768a019a64c48d676f`
- Executed rule hash: `c701ff882260`
- Counterexample: `checks/audit/87388eaff4ce/counterexample.json`
- Input: `checks/audit/87388eaff4ce/input.json`
- Racket output: `checks/audit/87388eaff4ce/racket.json`
- Rival output: `checks/audit/87388eaff4ce/rival.json`

Supported command, invoked from the packet root through the wrapper:

```bash
python3 run_with_racket.py python3 -m arcpuzzles apply \
  87388eaff4ce \
  --input ../checks/audit/87388eaff4ce/input.json \
  --out ../checks/audit/87388eaff4ce/racket.json
```

The transformation is not shown wrong. The defect is that ordinary lessons have
zero support for an output-relevant tie branch; only a special degenerate
texture reaches it. A model can therefore learn "sort by height only" from
normal generated data without contradiction. Target source left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-4bbe40f8398aea03-v0001/audit_assets.json), manifest SHA-256 `0f3d13a7dfc8e264cca4e67b31e1663154203e72c326038ae2fe6ce57f8ed55c`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `d4689258ca72838e9caaff746eb5fef2064103ac92f1946c0630365d9a41a1a7`.

# Decisions for 87388eaff4ce

## D1 — Preserve the canonical authority

**Decision.** Keep the canonical Racket program and rule hash `c701ff882260` unchanged.

**Original rationale.** The imported source did not document why the authority should change, and the baseline rule-smoke execution was already correct.

**Alternatives rejected.** Rewriting the rule, changing the tie-break, or refreshing approval metadata would conflate a data-distribution defect with semantic authority.

**Probe/evidence.** Canonical Python-mirror agreement, Racket parity, rule smoke, and authority synchronization pass in `checks/height-lesson/verification.json` and `checks/after-final/`.

**Failure mode/limit.** A future catalog change must be reviewed separately; this return does not approve one.

## D2 — Replace broad weak sampling with two exact canonical profiles

**Decision.** Restrict ordinary generation to `9×12` and `10×13` exact canonical profiles.

**Original rationale.** The prior broad dimensions appear intended to add diversity, but their documented rationale is unknown. In practice they coexisted with absent tie support and failed profile/contract quality.

**Alternatives rejected.** Keeping the old broad range and hoping rare ties appear; adding a special-only tie mode; or accepting envelope-only support. Those choices would leave normal lessons vulnerable to height-only inference.

**Probe/evidence.** `60/60` exact profile hits, 20 per band, in `checks/after-final/checks/87388eaff4ce_after_profile_floor.json`; 300-lesson coverage in `checks/lesson-census-v1.summary.json`.

**Failure mode/limit.** The distribution is intentionally narrow. It should be widened only with new exact profiles that retain all teaching witnesses.

## D3 — Use exactly three separated, distinct-color objects

**Decision.** Emit exactly three objects, each a separate 4-connected component with a distinct nonzero color.

**Original rationale.** The canonical examples use three objects and make the sorting rule inspectable. The imported generator's variable content did not ensure the tie branch was visible.

**Alternatives rejected.** Two objects provide fewer simultaneous confounds; four or more expand placement and shortcut interactions without adding evidence needed for this repair.

**Probe/evidence.** Canonical profile support and the source-bound verifier in `checks/height-lesson/verification.json`.

**Failure mode/limit.** This does not teach generalization to arbitrary object counts. A later extension should test count-generalization separately.

## D4 — Require all four semantic witnesses on every ordinary draw

**Decision.** Every draw must visibly exercise the equal-height color tie-break and refute height-only row order, cell-count-first, width-first, and ascending-height alternatives.

**Original rationale.** Unknown. The imported `2.0.1` sampler deliberately chose distinct heights, which made the canonical tie branch observationally dead on normal data.

**Alternatives rejected.** Statistical minimums such as one witness per 100 samples, or a dedicated special profile. Qwen training lessons are consumed individually; a lesson that never reveals a branch can teach the shortcut even if another lesson elsewhere is informative.

**Probe/evidence.** 72 focused generated samples in `checks/height-lesson/verification.json`, 300 production lessons in `checks/lesson-census-v1.json`, and the retained `counterexamples/teaching-witness-v1/`.

**Failure mode/limit.** The rival set is finite and declared. Undeclared rivals still require generic search, as shown by audit `d1dd527dba87`.

## D5 — Keep only two live exact controls

**Decision.** Advertise `grid_h` and `grid_w` only, with strict joint compatibility. Remove/retire dead `position_bias`, `density`, and texture controls from the public axis contract.

**Original rationale.** The prior controls appear intended as variation knobs, but their exact observable contract was undocumented and several were dead or degenerate.

**Alternatives rejected.** Silently accepting ineffective controls or coercing scalar values. Both make schedule claims unreproducible.

**Probe/evidence.** The final override matrix accepts all 810 lawful calls across nine cases and rejects an unknown key (`checks/after-final/checks/87388eaff4ce_after_override_results.json`).

**Failure mode/limit.** Because the axes form exact profile pairs, not every Cartesian combination outside the two profiles is lawful; incompatibility is explicit rather than silently remapped.

## D6 — Use strict validation and exhaustive placement backtracking

**Decision.** Enforce exact scalar types and grid/component/profile invariants; use randomized exhaustive backtracking for placements.

**Original rationale.** Unknown. The old self-check behaved like acceptance-only validation, and capped retry behavior could hide impossible schedules.

**Alternatives rejected.** Loose `int(...)` coercion, permissive unknown keys, and capped random placement retries.

**Probe/evidence.** Task regressions cover malformed controls and grids; the final self-check stage rejects all 57 destructive mutations; all 56 selected tests pass.

**Failure mode/limit.** Exhaustive search is practical only because the profile and shape vocabulary are bounded.

## D7 — Declare executable witnesses and competitors

**Decision.** Keep `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and `lesson_identifiable` close to the generator.

**Original rationale.** The previous source had no adequate executable lesson contract.

**Alternatives rejected.** Relying only on prose descriptions or canonical-pair correctness. Correct labels do not imply demonstrations identify the rule.

**Probe/evidence.** Required-rotation semantic evidence in `checks/after-semantic-gate-v2/` and the 300-lesson census.

**Failure mode/limit.** Generator authors can omit a plausible rival. Shared generic rival synthesis is therefore the top tooling recommendation in `FEEDBACK_TO_CODEX.md`.

## D8 — Retain a minimal task-local verifier and counterexample

**Decision.** Add `workspace/verify_height_lesson.py` and `counterexamples/teaching-witness-v1/`.

**Reason.** Future agents need a cheap source-bound check that can reproduce canonical compatibility, the exact teaching witness, and optional Racket parity without reconstructing this review.

**Alternative rejected.** Keeping only large battery logs, which are expensive to interpret and poor regression fixtures.

**Limit.** The verifier is task-specific; it is not a replacement for shared lesson-census tooling.

## D9 — Prototype one meaningful parameter, separate from production

**Decision.** Prototype `tie_break ∈ {color_asc,color_desc}`, chosen once per 3-demo/1-query episode, while retaining `color_asc` as the selected canonical rule.

**Alternatives rejected.** Varying grid size, shape, color palette, or distractor frequency: those alter inputs but not the executed rule. Independently resampling a tie-break per pair would make episodes incoherent.

**Probe/evidence.** Two complete episodes, two exact Racket programs, eight Racket-checked pairs, and alternate-setting refutation in `checks/parametric/87388eaff4ce-tiebreak.json`.

**Failure mode/limit.** Only two seeds are retained; no generic production parameter API is approved.

## D10 — Do not modify shared infrastructure in the selected-task patch

**Decision.** Keep shared-tool recommendations in `FEEDBACK_TO_CODEX.md`; include reusable task-local and audit probes in the return instead.

**Reason.** The assignment permits only selected-task source changes. A shared generic rival bank deserves its own review and regression suite.
