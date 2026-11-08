# Current notes: `77181d1aa16c` generator `4.0.0`

## Intended rule

Find the largest all-nonzero two-color rectangle. It is block 0 of a local 2×2 frame. Reflect it horizontally, vertically, and both ways into blocks 1–3. Sparse non-source cells inside those target blocks map the source's majority/minority roles to output colors. A missing role maps to 0. If the same block/role has multiple indicators, the first in row-major order wins.

Pinned selected-rule hash: `76ff7f3a7ec0`.

## Current construction

- Source: asymmetric strict-majority two-color rectangle, height/width 3–5.
- Margins: independently 0–2; the entire reflected frame must fit.
- Six deterministic geometry profiles include the canonical 10×10 / 4×4 / one-cell-margin profile and moved/rectangular alternatives.
- Four indicator profiles each create one missing descriptor and one conflicting duplicate descriptor.
- Exact axes: `pattern_h`, `pattern_w`, `top_margin`, `bottom_margin`, `left_margin`, `right_margin`, `indicator_profile`.
- Training lesson: 4 demonstrations + 1 query. The schedule period is 6.

## Reversed decisions

- **Old:** source fixed to the top-left half-grid. **New:** recover the largest all-nonzero rectangle. **Reason:** old validator rejected 8/8 canonical occurrences and omitted canonical geometry.
- **Old:** stale/singleton axes could be ignored. **New:** only exact, observable controls are exposed; invalid controls fail. **Reason:** baseline lint and retained override reproduction.
- **Old first repair:** any noncanonical source rectangle counted as a fixed-frame witness. **New:** the witness also requires actual output disagreement with the fixed-frame rival. **Reason:** retained seed `116417998598655`, index `4783`, where geometry differed but outputs agreed.
- **Old selected solution record:** behaviorally equivalent but textually divergent `target_code`. **New:** selected `target_code` exactly matches canonical; archival `raw_code` remains unchanged. Canonical authority and examples were not edited.

## Semantic contract

Declared rivals: last indicator wins; fixed canonical source; forced-square source; no reflection; carry source role when mapping is missing. Each has an executable witness relation and is checked by `lesson_identifiable`.

Final evidence, generator SHA `3300eb415d4a3cc51834b82a8d35017b6a08042c77af77df1b0efd1c4d5423ed`:

- 12/12 battery stages green, with required rotations.
- 50/50 focused tests passed.
- 120/120 generated inputs matched live Racket.
- 300/300 production lessons materialized; 0/300 ambiguous.
- 1,500/1,500 query rotations checked; 0 ambiguous.
- Task-local schedule probe: 36 windows, 180 rotations, 900 rival checks, 0 failures.

## Assumptions and limits

- Background is 0; source colors are the two colors in the largest all-nonzero rectangle with a strict majority ordering.
- Generated dimensions are intentionally bounded by 3–5 source sides and 0–2 margins.
- Symmetric source patterns are excluded because they fail to teach reflection.
- Evidence is finite and against five declared deterministic rivals only; unknown rivals remain possible.
- Production and rotation results assume the exported lesson contains five materialized pairs with four demonstrations.

## Reusable evidence

- Focused tests: `tests/test_generator.py`
- Cyclic schedule probe: `workspace/probe_schedule.py`
- Witness/rival agreement counterexample: `counterexamples/review-3fba77dccbdea44a/semantic-witness-agreement.json`
- Historical baseline audit used as lead: `counterexamples/review-9bcf85b162267497-v0001/`

## Current owner acceptance

Accepted v4.0.0 source geometry controls, largest-rectangle grammar and six-profile curriculum. Reviewer reports 50 portable tests, 12/12 stages, 300 lessons and 1,500 rotations. The fixed-query versus arbitrary-rotation distinction remains explicit in audits. Canonical rule unchanged; active target text synchronized and raw_code preserved. Semantic checks were not rerun. Generator approval binds these exact sources and does not admit model trajectories to training.
## Current reviewer considerations

Source SHA-256: `3300eb415d4a3cc51834b82a8d35017b6a08042c77af77df1b0efd1c4d5423ed`.

# Decisions — `77181d1aa16c`

## D1 — Recover the source by the selected rule, not by a fixed quadrant

- **Prior choice:** Treat the top-left half-grid as the source.
- **Original rationale:** Unknown; the baseline comments described a fixed 2P×2P layout even though the selected rule searches for the largest all-nonzero rectangle.
- **Failure mode:** All 8 canonical occurrences were rejected because canonical inputs have padding and a 4×4 source at `(1,1)..(4,4)`. A fixed-frame shortcut also fit all canonical labels.
- **Alternatives considered:** (a) special-case canonical 10×10; (b) continue fixed top-left generation but loosen only the validator; (c) make generation and validation follow largest-rectangle semantics.
- **Decision:** Choose (c). Both construction and validation now support moved and resized source rectangles.
- **Probe/evidence:** `checks/before/checks/77181d1aa16c_before_selfcheck.log`; canonical-focused tests; fixed-frame rival in the lesson contract.
- **Limit:** The generated rectangle is bounded to 3–5 by 3–5 with margins 0–2.

## D2 — Replace stale aliases and singleton controls with seven exact axes

- **Prior choice:** Advertise `grid_h`, `grid_w`, `pattern`, palette aliases, booleans, and fixed singleton values; most were not consumed by construction.
- **Original rationale:** Unknown; likely inherited generic generator metadata.
- **Failure mode:** Lint could not probe `pattern`, several axes had singleton domains, and requested dimensions could be silently ignored.
- **Alternatives considered:** Mark stale axes diagnostic; keep aliases for compatibility; remove them and expose only semantically observable controls.
- **Decision:** Expose only `pattern_h`, `pattern_w`, four margins, and `indicator_profile`. Each is exact, recoverable from the grid, and valid jointly.
- **Probe/evidence:** final override gate (`20,880/20,880` accepted, 0 findings) and `test_exact_joint_overrides_are_constructive_observable_and_label_safe`.
- **Failure handling:** Unknown keys, invalid types including `bool`, out-of-range values, negative sample indices, and unknown difficulty names raise `ValueError`.

## D3 — Use a six-profile deterministic curriculum

- **Prior choice:** Draw a random 3–5 square at the top-left and place six indicators at fixed corners/edges.
- **Original rationale:** Vary source size and colors while keeping generation simple.
- **Failure mode:** The distribution excluded canonical padding/origin geometry, never used rectangular sources, and did not guarantee every lesson refuted geometry shortcuts.
- **Alternatives considered:** Fully random legal geometry; rejection sampling until lesson-identifiable; a small deterministic schedule with randomized texture and palette.
- **Decision:** Use six geometry/indicator profiles. Profile 0 is canonical-like; profiles 1–5 move/resize the source and include rectangular cases. A deterministic schedule makes cyclic-start coverage auditable while texture and palette remain random.
- **Probe/evidence:** `checks/schedule-probe.json` and profile-floor report.
- **Limit:** Deterministic profiles can themselves become learnable metadata; semantic labels do not depend on profile index, and every profile is label-safe, but this is not a proof against all profile-conditioned shortcuts.

## D4 — Make first-wins and missing-role behavior observable in every generated grid

- **Prior choice:** One indicator per role/block with no guaranteed conflicting duplicate or missing mapping.
- **Original rationale:** Approximate the canonical indicator layout.
- **Failure mode:** Canonical pairs did not distinguish first-vs-last duplicate precedence, and carrying the source role when a mapping was absent could survive demonstrations.
- **Alternatives considered:** Rare stochastic edge cases; dedicated diagnostic-only examples; always include one missing descriptor and one conflicting duplicate.
- **Decision:** Every generated input contains one absent block/role mapping and one duplicated descriptor with different colors. Four `indicator_profile` values rotate which descriptors are affected.
- **Probe/evidence:** witnesses fire 600/600 for conflicting duplicate and missing role; named rival claims hold 60/60 each in final semantic gate.
- **Limit:** This deliberately concentrates training on these edge cases; it is appropriate for disambiguation but not an estimate of natural ARC frequency.

## D5 — Require asymmetric source patterns

- **Prior choice:** Random patterns could accidentally be symmetric.
- **Original rationale:** Randomness was expected to provide enough variation.
- **Failure mode:** A no-mirror/direct-tiling rival can agree whenever the source is symmetric.
- **Alternatives considered:** Measure and resample whole lessons; hard-code a pattern bank; construct random strict-majority patterns and reject symmetric ones.
- **Decision:** Construct randomized strict-majority two-color patterns and reject horizontal, vertical, and half-turn symmetry, with a deterministic fallback.
- **Probe/evidence:** asymmetry witness 600/600 and no-mirror rival claim 60/60.
- **Limit:** This excludes symmetric lawful inputs from training; they are intentionally omitted because they do not teach reflection.

## D6 — Treat witness names as exact separating claims

- **Prior choice in first repair:** `noncanonical_source_frame` meant only that the recovered source rectangle differed from `(1,1,4,4)`.
- **Failure mode:** Seed `116417998598655`, sample index `4783`, easy band has source rectangle `(2,1,4,4)`, yet the fixed-frame rival produces the same output. The witness fired while its named rival did not differ.
- **Alternatives considered:** Downgrade the witness to descriptive; lower a support threshold; tighten it to require actual separation.
- **Decision:** Tighten it. A witness listed in `WITNESS_RIVALS` fires only when its named rival disagrees with the selected rule.
- **Probe/evidence:** retained counterexample under `counterexamples/review-3fba77dccbdea44a/`; red→green focused test; final 60/60 claim checks.
- **Limit:** Computing the rival inside the witness is more expensive, but the grids and rival are small.

## D7 — Keep an independent Python mirror and live Racket parity checks

- **Prior choice:** Generator had no executable mirror/rivals.
- **Original rationale:** Labels are supplied by Racket at export time.
- **Failure mode:** Generator-side semantic hooks could silently encode a different rule; validator correctness alone would not detect label drift.
- **Decision:** Add `rule_mirror`, compare it with all 8 canonical occurrences and 120 live Racket applications, and use it for local rival scoring.
- **Probe/evidence:** `checks/after-final/..._rule_smoke.json`; 120/120 parity, 0 crashes/mutations.
- **Limit:** The mirror is independent in implementation but reviewed in the same return; live Racket remains the authority.

## D8 — Text-synchronize the selected augmented authority, preserve archival source

- **Prior choice:** Selected augmented `target_code` was behaviorally equivalent but normalized to hash `55ce970febd1`, not canonical `76ff7f3a7ec0`.
- **Original rationale:** It was an unsynced beautification.
- **Failure mode:** Strict defect lint emitted `rule-source-divergence`; future reviewers could not tell intentional equivalence from authority drift.
- **Alternatives considered:** Ignore warning because sampled behavior matched; change canonical; synchronize the selected copy only.
- **Decision:** Synchronize only selected `target_code` to canonical. Preserve `raw_code` unchanged as archival provenance. Do not alter canonical examples or canonical authority.
- **Probe/evidence:** exact-sync regression failed before the edit and passes after; final defect lint/authority sync green.

## D9 — Require arbitrary query rotations for this curriculum

- **Prior choice:** Production uses the fifth pair as query; rotation safety was not established.
- **Rationale for change:** Downstream assembly may rotate pairs, and four demonstrations should identify the same rule regardless of which pair is held out.
- **Decision:** Run the strict semantic gate with required rotations, a 300-lesson census with all five query positions, and a cyclic-start task probe.
- **Evidence:** 0/1,500 census rotations ambiguous; 0/180 schedule-probe rotations failed.
- **Limit:** These checks cover five declared rivals only. They are evidence of bounded curriculum robustness, not a proof of unique induction.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/77181d1aa16c/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->

## 2026-10-25 native parametric review — mapping policy

- Added task-local `mapping_policy=local_blocks|dominant_block`; the default returns the selected canonical Racket source byte-for-byte.
- The alternate infers each target block's ordered role mapping and support count, selects the unique most-supported block, then uses that selected mapping to recolor all three mirrored targets.
- Inputs are matched across settings and support 2–6 demonstrations plus four prefix-stable queries at 14×16, 18×20, 24×27, and 30×30.
- A finite audit covered 12 episodes, 92 label claims, nine executable shortcut rules, 41 distinct protected-Racket executions, and 16 public views with no findings. This is bounded evidence, not a universal uniqueness proof.
- Native qualification passed both settings at seeds 0 and 17 with 3 demonstrations and 4 queries (40 protected-Racket evaluations). The source-bound wrong-selected-block witness was replayed and changes the final output.
- Production `generator.py` and canonical authority were not changed. Owner exact-source integration, fresh native acceptance, and any training-admission decision remain pending.
