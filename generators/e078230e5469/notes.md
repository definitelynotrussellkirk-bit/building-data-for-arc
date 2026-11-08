# Current notes: e078230e5469

## Intended rule and authority

The input is `s × (3s+2)` with three equal square panels separated by full color-5 columns. Infer the unique D4 transform mapping panel A to panel B and apply it to panel C. The selected canonical Racket authority was not changed. Its normalized hash is pinned as `RULE_HASH = "b95936763d1c"`.

Current generator version: `4.0.0`; final reviewed SHA-256: `59b1968c4dd607a2efec8ff9d712b91651d72415dd36f7d4fdd704e9fd192056`.

## Reversed decisions

Version 3.0.1 advertised eight boilerplate controls, excluded identity, selected transforms randomly, and sampled disconnected Bernoulli motifs. Two retained source-bound audits (`review-39fda8e58e9e1c0d:v0001` and `review-aaaca94facfaf522:v0001`) showed that invalid transforms, palettes, and unknown controls could be ignored or replaced, while a globally advertised size could fail in a band.

Version 4.0.0 instead exposes only three meaningful exact controls:

- `square_size`: 3, 4, 5, or 6;
- `transform`: all eight D4 elements, including identity;
- `palette_kind`: default, warm, cool, or varied, visibly encoded by exemplar/query color roles.

Unknown keys, invalid values, malformed seed/sample index, and invalid difficulty are rejected. `observe_overrides` reconstructs all three controls from a valid returned grid.

## Distribution and lesson policy

Ordinary motifs are monochrome, 4-connected, 3–7 cells, and have full eight-image D4 orbits. This makes A→B unique and makes C distinguish every transform. Every sliding eight-draw window covers all transforms. Every fourth draw uses size 5 in every difficulty band, preserving canonical-profile support while retaining size variation.

Lessons use five ordered demonstrations and one query. Declared competitors include every fixed transform, copying panel B, and a canonical-fitting shortcut that handles only the three transform families observed in canonical examples. `lesson_identifiable` requires valid authoritative labels, at least two transform branches, and refutation of every declared competitor.

## Final evidence

- Battery: 12/12 green at `checks/after-final/checks/e078230e5469_after_battery_summary.json`.
- Focused portable tests: 10/10 at `checks/task-tests-final/result.json`.
- Override contract: 8,730 draws, zero findings at `checks/after-final/checks/e078230e5469_after_override_results.json`.
- Profile floor: 19/60 exact hits and support in every band at `checks/after-final/checks/e078230e5469_after_profile_floor.json`.
- Lesson census: 300/300 materialized, 0/1,800 production ambiguities, 0/1,800 rotation ambiguities, 1,798 unique inputs at `checks/lesson-census-final.summary.json`.

## Known limits and open findings

The declared-rival set and finite census do not prove universal identifiability. The deterministic schedule should be shuffled by downstream exporters so global record order is not a model feature. `schedule_profile` is exhaustively checked at all cyclic starts by the task-local tests, but there is no shared period-enumeration receipt attached to the ordinary battery. Authority sync also notes an older divergent archival raw-code representation; selected execution parity passes and no authority change is proposed.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-aaaca94facfaf522:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `8e03c70c71ca71fd46bdf79ded16624ea2ee346b04b4229006dad85269921273`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Accepted source SHA 59b1968c4dd607a2efec8ff9d712b91651d72415dd36f7d4fdd704e9fd192056 replaces ignored/invalid controls with strict observable axes. tests/test_generator_e078230e5469.py and counterexamples/review-3e12fd663a54e1d4/override_contract_regression.json retain regressions; reviewer reports 8730 exact override draws and 10 portable tests passing. Explicitly resolve prior ignored/invalid override finding; no maintainer rerun.

### Assessment or prior finding

## e078230e5469

**Concrete defect: accepted overrides can be silently ignored or replaced.** The generator declares exact axes including `transform` and `palette_kind`, but `generate(19, 3, difficulty="medium", transform="bogus")` returns a valid grid instead of rejecting the invalid value. On that exact replay, the baseline call, invalid-transform call, `palette_kind="warm"`, `palette_kind="cool"`, and unknown `typo_axis=123` call are byte-identical; each has SHA-256 `f1a383c4107e8233c535703c55917a29449aeb1d67b28c3ada776379ea99cec8`, shape 5×17, and `self_check == []`.

This is adversarially important because a curriculum builder can believe it requested a particular dihedral transform or palette contrast while the generator quietly substitutes the random default. The semantic scene may still be valid, so ordinary self-checking does not reveal that the intended lesson was never emitted. Evidence: `checks/audit_probe.json`.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-aaaca94facfaf522-v0001/audit_assets.json), manifest SHA-256 `c91eca1d81fc3b7817ed2e5a8f43ee6ea4242b86f127d95c48e6aac14a48ffa5`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `59b1968c4dd607a2efec8ff9d712b91651d72415dd36f7d4fdd704e9fd192056`.

# Decisions for e078230e5469

## D1 — Narrow the advertised surface to three exact, observable axes

**Prior choice.** Version 3.0.1 advertised eight standard-form axes, including aliases and singleton controls (`palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`). The original rationale is not recorded. Retained audits showed that several controls were ignored and unknown keys were accepted.

**New choice.** Advertise only `square_size`, `transform`, and `palette_kind`. Each has a finite domain, is honored in all bands, and is recoverable from pixels by `observe_overrides`.

**Alternatives rejected.** Implementing all boilerplate axes would add aliases with no meaningful independent effect; silently retaining them would preserve false provenance. Exact incompatibility declarations were unnecessary because all 3×4×8 combinations are legal.

**Probe and failure mode.** The focused test exercises 192 joint boundary combinations. The shared override checker adds 8,730 seeded calls. Unknown keys and invalid values must raise rather than fall back. Evidence: `checks/after-final/checks/e078230e5469_after_override_results.json`.

## D2 — Generate all eight D4 transforms, including identity

**Prior choice.** The baseline excluded identity and randomly selected among seven nonidentity transforms, likely to avoid A→B ambiguity and identity-looking outputs.

**New choice.** Include identity as an ordinary branch. Identity is part of the selected Racket authority, and omitting it teaches an incomplete rule. Both A and C now have full eight-image D4 orbits, so even an identity demonstration identifies exactly one branch and query outputs remain separating.

**Alternatives rejected.** Keeping only the seven nonidentity branches would preserve a systematic blind spot. Allowing arbitrary/symmetric motifs would make identity and reflections ambiguous.

**Probe and limitation.** All eight witnesses fire in the semantic gate, and every eight-draw window contains all eight transforms. This guarantees branch support for the deterministic schedule, not uniformity under every external resampling scheme.

## D3 — Use a deterministic eight-transform coverage schedule

**Prior choice.** Independent random branch selection could create five-example lessons with weak or repeated evidence.

**New choice.** `schedule_profile(seed, sample_index)` cycles over the eight D4 transforms. Every sliding window of eight draws covers each branch exactly once; every five-draw lesson has five distinct branches.

**Why five demonstrations.** The canonical examples are fit by a plausible shortcut that handles only `{rot90, flip_v, transpose}` and otherwise returns identity. A five-distinct-transform window must contain at least one branch outside that three-branch family plus identity, so it refutes that shortcut. It also refutes every fixed-transform rival and `copy_panel_b`.

**Alternatives rejected.** Pure random sampling has nonzero weak-window probability and would need rejection sampling. A hand-picked canonical-only schedule would reinforce the shortcut. A larger mandatory lesson would add cost without improving the declared-rival result.

**Probe and limitation.** The task test checks all eight cyclic starts, all bands, and four seeds. The 300-lesson census checks the actual production assembly and all six query rotations. The schedule is not declared as a shared `LESSON_SCHEDULE_PERIOD`; current source-bound task tests provide the exhaustive cyclic-start receipt, while the standard battery samples the schedule. Downstream exporters should shuffle records so global order is not itself learnable.

## D4 — Anchor the canonical 5×17 profile in every band

**Prior choice.** Easy used sizes 3–4 and hard used 5–6, so an exact canonical-profile row was not guaranteed per band.

**New choice.** Every fourth draw uses `square_size=5`; other residues remain difficulty-shaped. This preserves easy/hard variation while guaranteeing exact support.

**Alternatives rejected.** Making all rows size 5 would pass the floor but collapse shape diversity. Relying on chance would make a required gate flaky.

**Measured result.** The final 60-draw profile check found 19 exact hits and 19 envelope hits, with nonzero exact support in every band.

## D5 — Make palette regimes visually recoverable

`warm` draws both role colors from `{2,4,7,9}`; `cool` draws both from `{1,3,6,8}`; `default` uses cool exemplar/warm query; `varied` uses warm exemplar/cool query. The two role colors are always distinct, separator color 5 is reserved, and the regime can be reconstructed from the returned grid.

A nominal palette label with no pixel effect was rejected because it is unusable for controlled data generation. The main limitation is semantic: ARC color names such as “warm” and “cool” are only categorical buckets here, not a task rule.

## D6 — Use connected sparse motifs with full D4 orbits

The baseline sampled each cell independently, which could create disconnected and morphology-poor patterns. The repair grows 4-connected supports and rejection-samples until every D4 transform is distinct. Motifs contain 3–7 cells and remain monochrome.

This choice simultaneously supports canonical morphology, unique A→B inference, and query separation. The rejected alternative was to repair ambiguity only after generation; constructing valid supports directly gives a clearer invariant and stronger tests. Sampling is bounded at 512 attempts and has not failed in the final test/battery ranges, but the bound is still an implementation limit.

## D7 — Validate the complete call contract before generation

`seed` and `sample_index` must be literal integers (not booleans), sample index must be nonnegative, and difficulty must be `None`, `easy`, `medium`, or `hard`. Unknown override keys and out-of-domain values are rejected before a grid is returned.

This reverses the baseline fallback behavior, where an invalid transform was replaced by a random transform. The focused scalar test was added after the intermediate defect-lint failure and was first observed red in `checks/tdd-red-scalars.log`.

## D8 — Declare executable semantic rivals and lesson checks

The generator declares eight fixed-transform rivals, `copy_panel_b`, and `observed_transform_family_only`; the last also appears as `CANONICAL_SHORTCUTS` because it fits all three canonical pairs. Each transform has a witness and explicit rival obligations. `lesson_identifiable` checks labels against the selected-law mirror, requires at least two distinct branches, and rejects any lesson leaving a declared competitor alive.

A rival-free “all labels are individually correct” check was rejected because it does not establish that a lesson teaches the intended rule. The finite competitor set remains a limitation; unknown shortcuts can still exist.

## D9 — Keep Racket authority unchanged

The selected canonical rule already implements the intended three-panel D4 analogy and matches all canonical outputs. The repair therefore pins `RULE_HASH="b95936763d1c"` but changes no Racket source. This minimizes authority risk and makes all distribution/lesson changes independently reviewable.

## D10 — Preserve failures and use the final bytes for the solve

The incomplete before battery, first red tests, intermediate 10-green/2-failed battery, and interrupted first final run were retained. The final battery was resumed only with unchanged sources. The post-repair solve was prepared after the final source hash was fixed and records earlier exposure honestly.
