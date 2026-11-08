# Working notes: db89dc496d45

## 2026-10-07 review `review-5b7135027d4b402a`

The imported v2.0.0 generator made every sampled input solvable by global nonzero color frequency: 4,000/4,000 baseline draws matched that shortcut, and one draw failed `self_check`. The advertised override surface also contained ignored, constant, or validator-incompatible controls.

Version 3.1.2 replaces best-effort placement with four separated macro-regions, exposes one exact `scene_profile` override, and alternates two semantic witnesses. Split-distractor examples refute top-color aggregation; split-target examples refute the stronger conditional “choose the second color when the top is disconnected” and single-component-color rules. Witness type and target size are seed-decoupled from exact dimensions.

The selected task-local Racket `target_code` was synchronized exactly to the canonical selected rule. Rule behavior and `RULE_HASH = 56bd46ef5a5e` are unchanged; archival `raw_code` was intentionally preserved byte-for-byte.

Reusable probe: `workspace/shortcut_probe.py`. It verifies canonical fit, generated rival disagreement, every held-out-query rotation, unique inputs, and per-profile witness support. Its pass is finite evidence only; generated morphology remains four separated 4×5 corner regions.

See packet-return evidence under `checks/`, especially `shortcut-probe.json`, `lesson-census.json`, and the retained red regressions for stronger-rival and profile/size leakage.
## Current reviewer considerations

Source SHA-256: `df41a86bd58964a2bc83f4cd4d63478c9c6a06a1bd708e30d0b6f9c823f7859c`.

# Design and review decisions for `db89dc496d45`

## D1 — Preserve the rule; repair the curriculum

**Original rationale:** the imported v2.0.0 comments claimed four demonstrations distinguished “crop smallest,” “crop by color,” whole-grid output, and removal. That rationale did not test disconnected repetitions of a color. The exact reason for the nine advertised axes and degenerate textures is otherwise unknown.

**Probe:** I implemented a baseline rival that aggregates all nonzero cells by color and crops the most frequent color. It matched the intended connected-component result on all 4,000 sampled generator inputs and on all five canonical pairs (`checks/before-shortcut-probe.json`, `checks/shortcut-probe.json`).

**Choice:** keep the canonical rule `(extract-largest g 0)` and make generated lessons distinguish objects from colors. The rule is coherent; the input distribution was the defect.

**Rejected alternatives:**

- Changing the rule to “most frequent color” would merely codify the accidental shortcut and contradict the connected-component task.
- Randomly reusing colors without a lesson contract could introduce ambiguous ties or still leave conditional shortcuts.
- Merely declaring a rival without forcing witnesses would make the semantic gate descriptive rather than protective.

**Failure modes addressed:** aggregation across disconnected cells, selecting the largest fragment of the top color, selecting the second-ranked color when the top is split, and ignoring all colors that appear in multiple components.

## D2 — Use two alternating semantic witness profiles

**Choice:** every draw belongs to exactly one of two profiles:

- `split_distractor_color_dominates_by_total`;
- `split_target_color_dominates_by_total`.

For a fixed lesson seed, the profile alternates by sample index. Four demonstrations therefore include both witness types under any contiguous production start and under every held-out-query rotation of a five-pair window.

**Why two profiles:** the first repair generated only a disconnected distractor whose aggregate count exceeded the target. That refuted global frequency, but it made the intended target consistently the second-ranked color whenever the top color was split. The regression in `checks/stronger-rival-red.log` captured the surviving rule before the second profile was added.

**Rejected alternative:** adding more distractor colors without changing the target color's connectivity. That adds visual diversity but does not refute the conditional shortcut.

**Limitation:** this is finite adversarial coverage, not proof of unique induction. Four executable rivals are declared because they are both canonical-fitting and structurally plausible.

## D3 — Separate lesson semantics from visible schedule features

**Initial failure:** witness type was coupled to sample-index parity, while dimensions follow a six-position schedule. Exact dimensions therefore leaked witness type. Target size was also a deterministic function of schedule position.

**Choice:**

- canvas profile remains public and cyclic by sample index;
- witness type uses `((seed // 8) + sample_index) % 2`;
- target size uses `5 + ((seed + sample_index) % 8)`.

This preserves alternation inside a lesson while making each exact dimension support both witnesses and every target size 5–12 across seeds.

**Evidence:** the pre-fix failures are retained in `checks/profile-decouple-red.log` and `checks/size-decouple-red.log`. Final support counts are in `checks/shortcut-probe.json`.

**Rejected alternative:** purely random witness selection. It would require rejection/resampling to guarantee each four-demo window contains both witnesses and would complicate deterministic replay.

## D4 — Replace nine nominal axes with one exact public control

**Original state:** `grid_h`, `grid_w`, palette aliases, constant-valued controls, density, texture, and degenerate textures were advertised. Several were ignored or incompatible with the validator, unknown keys were accepted, and exact dimensions were not honored.

**Choice:** expose only `scene_profile`, with six literal valid values. `observe_overrides` recovers the exact profile from dimensions. Unknown keys, wrong types, and invalid values reject.

**Why fixed profiles:** dimensions are pedagogical context, not the semantic rule. A small explicit schedule gives canonical-size coverage plus larger canvases while making the override contract exact and cheap to verify.

**Rejected alternatives:** retaining no-op controls for backward appearance, or keeping degenerate textures in the production API. Those controls had no lawful output label or contradicted the unique-largest-component domain.

## D5 — Construct placement instead of retrying best-effort placement

**Original failure:** `_try_place` returned `False` after 60 attempts, and callers ignored the return value. This caused at least one baseline input to omit required components and fail `self_check`.

**Choice:** reserve four corner macro-regions separated by blank gutters. Each role is always painted into one region, so objects cannot be silently omitted or merge across roles.

**Rejected alternative:** increase retry counts. That reduces but does not eliminate failure and makes coverage dependent on canvas crowding.

**Limitation:** the four-corner, 4×5 morphology is narrower than the complete lawful domain. It is acceptable for this curriculum because colors, roles, shapes, sizes, dimensions, and region assignment vary, but it remains a documented support restriction.

## D6 — Preserve nontrivial crop shape

**Failure:** the first repaired generator occasionally produced a component whose bounding box was completely filled. The output then became a single solid color, which the defect lint flagged (`checks/after-solid-failure-run.log`).

**Choice:** regenerate target shapes until the bounding-box area exceeds component size, with a deterministic connected sparse fallback. This ensures the crop encodes shape rather than only color and dimensions.

## D7 — Synchronize selected authority text without replacing archival source

**Original state:** canonical and selected rule carriers executed identically, but the selected task-local text differed. The archival `raw_code` was a much larger search source.

**Choice:** copy the exact canonical selected source into `racket_target.target_code`; do not edit `raw_code`. This makes the selected authority exact while preserving provenance.

**Verification:** final authority sync and Racket execution pass. Rule hash and behavior are unchanged. The archival raw source remains 96,560 bytes, SHA-256 `a244e6d3cb243225847fb21b6e451c728ffa68032cf7e1f06f1189bc68aced44`.

## D8 — Build a reusable, source-bound shortcut probe

`repo/generators/db89dc496d45/workspace/shortcut_probe.py` discovers the generator's declared rivals and witnesses instead of hard-coding expected names. It checks canonical fit, generated disagreement, every held-out-query rotation, unique-input counts, and per-profile witness support. It refuses to report success if a rival is never contradicted, a rotation is ambiguous, or dimensions reveal witness type.

The probe is intentionally finite. It records source/rule hashes and its sampling policy so a future agent can extend it rather than treating its pass as universal proof.

## 2026-10-25 reviewer parametric proposal: largest-size color relay

**Decision.** Preserve the exact canonical `extract-largest` Racket source as
`mode=largest_component`. Add `mode=largest_size_relay`: find the unique largest
4-connected monochromatic component, use its cell count as an input-dependent
key, then select the different color whose total disconnected cell count equals
that key and crop the union of that color. Every scene also contains a unique
non-source `key+1` decoy, so replacing the intermediate by `size+1` changes the
selected color and final grid.

**Construction.** Inputs are identical across settings, support 2..6
demonstrations and exactly four prefix-stable queries, and include a 30x30 query
whose relay union spans both corners. The first two demonstrations put the relay
at frequency ranks 2 and 4; source-colored remote fragments, split relay pieces,
and the `key+1` decoy refute envelope, single-component, fixed-rank, and
wrong-intermediate shortcuts.

**Evidence.** 78 staged tests pass. A 64-seed audit covers 640 episodes and
5,120 distinct labeled pairs with zero surviving declared rivals; 42 protected
Racket evaluations include a seed-17 causal witness (`key=12`, wrong key 13)
whose correct and wrong programs produce different outputs. Native qualification
covers both settings at seeds 0 and 17 with 40 protected-Racket evaluations.
Sixteen sequential one-query public projections verify source binding, visible
byte hashes, and private/future-query separation. See
`workspace/parametric/evidence/manifest.json`,
`workspace/parametric/evidence/current/self_audit.json`, and
`checks/db89dc496d45/qualification/qualification.json` in the return package.

**Status/limit.** Reviewer-reported native qualification only. Owner acceptance,
fresh integration replay, measured training value, and training admission remain
pending. The production generator and selected canonical rule were not changed.
