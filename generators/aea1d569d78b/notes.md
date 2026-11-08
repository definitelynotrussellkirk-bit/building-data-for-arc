# Working notes: aea1d569d78b

## Review lead and baseline

No associated prior-review notes were present; `evidence/associated_notes.jsonl` was empty. The imported `2.0.1` generator and its summary were therefore the only lead. They described a horizontal-row rule, although the pinned Racket authority also connects vertical pairs.

The required before battery, bound to generator SHA-256 `e0a0ce74c339a8b0a74a6b5ec4e86b76e6fef4172e5286faf44798c53c925efc`, finished with 5 green, 2 advisory, and 5 failed stages. The failures were `lint`, `defect_lint`, `dist_gate`, `override`, and `authority_sync` (`checks/before/checks/aea1d569d78b_before_battery_summary.json`). Concrete baseline problems:

- generation covered horizontal clear pairs only, omitting the authority's column behavior;
- advertised palette controls never affected output, which used only colors 0 and 1;
- adjacent sampled columns could silently skip a requested pair;
- degenerate textures were admitted as teaching data;
- `self_check` checked little beyond shape and the presence of blue;
- no executable semantic witnesses or rivals were declared;
- no pinned `RULE_HASH` was present; and
- the base authority's `target_code` differed from `raw_code` only by comments, failing exact synchronization.

## Repair

Version `3.0.0` replaces the misleading nine-axis surface with two exact, observable controls: four canonical canvas profiles and the blocked pair's orientation. Every lawful draw has six blue cells inducing exactly three disjoint endpoint pairs: one clear horizontal, one clear vertical, and one blocked pair. Two distinct singleton distractor colors preserve the canonical four-color palette cardinality. The blocker is sampled from nonzero colors excluding `5`, while the second distractor may include `5`.

The non-5 blocker is deliberate. All five canonical pairs are compatible with the shortcut “only color 5 blocks,” because the only canonical blocked path uses color 5. A generated color-8 witness refutes that shortcut under the Racket authority (`checks/shortcut-aea1d569d78b/`). Each draw also refutes horizontal-only, vertical-only, connect-through-blockers, and identity. Clear horizontal and vertical paths each contribute at least one output cell not supplied by the other orientation, so crossing layouts cannot accidentally hide an orientation.

Difficulty now changes composition: easy is separated, medium is a deterministic mix, and hard crosses the two clear paths. An intermediate source had identical band distributions and correctly failed `defect_lint`; that retained failure is `checks/after-final/checks/aea1d569d78b_after_battery_summary.json`. The final band behavior repaired it.

`rule_mirror`, `strict_canonical_like`, semantic witnesses/rivals, and `lesson_identifiable` support task-local and shared checks. The Racket algorithm was not changed. Only the duplicated `target_code` text in `repo/shared/data/base/solutions/banks/d3d681cdb82a/E51__aea1d569d78b.json` was synchronized exactly to `raw_code`.

## Verification summary

Final generator SHA-256: `8547ba66930b3c01c56b2f424de3da4b265d4ff36e4f7296ca364ebeb020d4ba`.

- Final battery: 12/12 green (`checks/after-final2/checks/aea1d569d78b_after_battery_summary.json`).
- Portable task tests: 44/44 passed (`checks/task-tests-final/result.json`).
- Shared Racket-backed census: 300 lessons, 1,200 pairs, 1,200 held-out-query rotations, 1,200 unique inputs, 0 ambiguities (`checks/lesson-census-final.json`).
- Task-local exhaustive cyclic probe: 300 samples and 900 three-example rotations, 0 failures (`checks/task-semantic-probe.json`).
- Post-repair visible solve: 3/3 demonstrations on the first attempt, with earlier rule exposure declared (`solve/summary.json`).

## Limits

The canvas and palette profiles are intentionally canonical-like rather than exhaustive over all lawful ARC grids. Semantic results quantify only the declared rivals; they do not prove universal rule uniqueness. The production sampler is randomized but deterministic per key and uses a validated deterministic fallback if bounded rejection sampling cannot place a scene.
## Current reviewer considerations

Source SHA-256: `8547ba66930b3c01c56b2f424de3da4b265d4ff36e4f7296ca364ebeb020d4ba`.

# Decisions — aea1d569d78b

Final generator SHA-256: `8547ba66930b3c01c56b2f424de3da4b265d4ff36e4f7296ca364ebeb020d4ba`.

## D1 — Follow the pinned row-and-column authority

**Choice.** Teach connections in both rows and columns, with all interior-clear tests evaluated against the original input.

**Original rationale.** Unknown. The imported `2.0.1` summary and implementation described rows only, but the pinned Racket source had always performed a row pass followed by a column pass. No associated prior notes were present.

**Alternatives considered.** (a) Narrow the Racket rule to horizontal only; rejected because the canonical authority and canonical outputs already support the two-orientation rule. (b) Leave the sampler horizontal-only and rely on canonical examples to teach columns; rejected because generated lessons would systematically reinforce the wrong scope.

**Probes.** All five canonical pairs pass `strict_canonical_like`, and `rule_mirror` matches every canonical output. Final `rule_smoke`, `racket_lint`, and `authority_sync` stages are green. The post-repair visible solve inferred the two-orientation rule from three generated demonstrations and passed 3/3 visible examples on its first attempt.

**Failure modes and limits.** The Python mirror is independent reviewer tooling, not label authority. Any future Racket semantic change requires a new `RULE_HASH`, refreshed parity tests, and re-evaluation of every declared rival.

## D2 — Use the four canonical dimension profiles

**Choice.** Sample exactly `8×10`, `9×8`, `9×9`, and `10×10` through the exact `canvas_profile` override.

**Original rationale.** The baseline advertised broad ranges (`7..12` by `8..14`), but no evidence explained them. The five canonical inputs use exactly the four selected profiles.

**Alternatives considered.** (a) Keep broad independent height/width axes; rejected because they inflated the override surface without teaching a rule distinction and made canonical-profile coverage less direct. (b) Fix one size; rejected because it would introduce a needless size shortcut. (c) sample every dimension in the old ranges; unnecessary for the current repair and less canonical-like.

**Probes.** Tests force all 4 profiles × 2 blocked orientations × 4 difficulty labels. In 100 samples per band, every profile appeared; the shared `profile_floor` and override gates pass.

**Failure modes and limits.** Dimension generalization outside these four profiles remains untested. The rule itself is dimension-agnostic, but this curriculum intentionally favors canonical support over exhaustive size coverage.

## D3 — Match canonical object count and palette cardinality

**Choice.** Generate exactly six blue cells and exactly two distinct singleton distractor colors, for a four-color input palette including background and blue. Color `3` is output-only.

**Original rationale.** Unknown for the baseline’s variable `2..5` horizontal pairs. Every canonical input has six blue cells and palette `{0,1,5,6}`.

**Alternatives considered.** (a) Vary pair count; rejected because the previous placement loop could underproduce the requested count and variable counts did not repair the semantic omissions. (b) Use only colors 0 and 1; rejected because it makes blocker behavior impossible to teach and leaves advertised palette axes dead. (c) copy canonical colors 5 and 6 exactly; rejected because color-role variation is needed to refute a canonical-fitting shortcut.

**Probes.** `self_check` enforces six blues, three induced pairs, exactly two singleton distractors, and no input green. The 300-sample probe observed 19–21 distinct palettes per band, and all canonical pairs remain owned.

**Failure modes and limits.** Distractors are singleton objects by design; the curriculum does not test large unrelated objects or repeated blocker colors. Colors are varied only where the Racket rule treats them interchangeably as nonzero blockers/distractors.

## D4 — Put a complete semantic lesson in every generated grid

**Choice.** Every main-path grid contains one clear horizontal pair, one clear vertical pair, and one blocked pair. Each blue endpoint belongs to exactly one pair.

**Original rationale.** The baseline’s distinct-row and nonreused-column constraints seem intended to simplify pairing, but no rationale was retained. They also prevented vertical examples.

**Alternatives considered.** (a) Teach horizontal, vertical, and blocking evidence across separate demonstrations; rejected because arbitrary query rotations could then expose incomplete demonstration subsets. (b) allow accidental extra row/column pairs; rejected because six endpoints could induce unintended semantics. (c) use degenerate blank or single-endpoint textures; rejected as nonteaching identity cases.

**Probes.** Every one of 300 sampled grids independently refuted every declared rival. The shared census found 0 ambiguities across 300 production lessons and 1,200 held-out-query rotations. The task-local probe checked all cyclic starts of three-example windows and each of the three held-out positions: 900/900 passed.

**Failure modes and limits.** “Complete in one grid” is intentionally stronger than the minimum needed for a three-demo lesson. It reduces curriculum variety but makes lesson assembly robust to reordering and query choice.

## D5 — Use a non-color-5 blocker

**Choice.** The blocked pair’s blocker is sampled from `{2,4,6,7,8,9}`. A second singleton distractor is sampled from the remaining legal distractor colors and may be `5`.

**Original rationale.** The baseline had no blockers. In the canonical data, the only blocked path contains color `5`, so the rival “only color 5 blocks” fits all 5/5 canonical pairs.

**Alternatives considered.** (a) use only color 5 blockers; rejected because it preserves the shortcut. (b) mix 5 and non-5 blockers probabilistically; rejected because some individual lessons would remain compatible with the shortcut. (c) omit color 5 entirely; rejected because retaining it as an irrelevant distractor better separates color identity from blocking status.

**Probes.** The exact easy-band seed `610000`, sample index `0`, contains a color-8 blocker. Racket and `rule_mirror` agree; the color-5-only rival differs at four cells (`checks/shortcut-aea1d569d78b/comparison.json`). Every sampled grid hit the non-5 blocked-pair witness.

**Failure modes and limits.** The declared shortcut set is not exhaustive. For example, a learner could invent a different color subset from finite data; palette diversity reduces but cannot eliminate all such hypotheses.

## D6 — Guarantee orientation-exclusive output cells

**Choice.** Clear horizontal and vertical paths may cross, but each orientation must paint at least one interior cell not also painted by the other.

**Original rationale.** This condition was added after a focused test exposed a crossing where a one-cell horizontal segment lay entirely on the vertical path. On that scene, a vertical-only rival accidentally matched the complete output.

**Alternatives considered.** (a) forbid crossings everywhere; rejected because crossings are useful compositional difficulty and test original-input semantics. (b) keep crossings and merely declare orientation rivals; rejected because declarations without guaranteed refutation are not a semantic contract. (c) require long spans globally; more restrictive than necessary.

**Probes.** The regression test was written before the repair and observed failing rival behavior. Final tests and the 300-sample probe report 300/300 refutations for both horizontal-only and vertical-only.

**Failure modes and limits.** The check handles the declared orientation rivals. It does not enumerate every partial-orientation policy a learner might invent.

## D7 — Make difficulty semantically observable

**Choice.** Easy uses separated clear paths, hard requires a clear-path crossing, and medium deterministically mixes the two based on its keyed RNG.

**Original rationale.** The baseline varied dimensions and pair count by band. Once dimensions and pair count were aligned to canonical profiles, that old difficulty mechanism no longer applied.

**Alternatives considered.** (a) leave bands identical; rejected after the retained intermediate battery failed `defect_lint`. (b) make hard larger; rejected because canvas profile is an independently exact control and size is not the core composition. (c) add more blockers in hard; rejected because it would change the fixed three-signal lesson design.

**Probes.** The intermediate source SHA `cc91b4cc471d74c52c6e7829a4ef22d52903272e997342d3e09f747632c68740` passed 11/12 battery stages but failed `defect_lint` for dead bands. Under the final source, the task-local 100-per-band probe observed crossings `0/100` easy, `56/100` medium, and `100/100` hard; final `defect_lint` is green.

**Failure modes and limits.** Difficulty is compositional, not a calibrated psychometric score. Medium’s 56/100 retained sample is an observed seeded proportion, not a promised global probability.

## D8 — Keep only truthful exact overrides

**Choice.** Advertise `canvas_profile` and `blocked_orientation`; reject unknown keys and invalid values; expose `observe_overrides` for independent realization checks.

**Original rationale.** The baseline exposed nine controls, several fixed to one value and at least one (`palette_kind`) operationally inert. No retained rationale justified that surface.

**Alternatives considered.** (a) preserve aliases for compatibility; rejected because a reviewer contract should not claim controls that cannot be observed. (b) expose blocker color or crossing as exact axes; not needed for the assignment, and difficulty already owns crossing composition. (c) retain degenerate textures; rejected because they are not main-path teaching examples.

**Probes.** Tests cover every legal exact-axis combination and malformed/unknown overrides. The final override stage reports PASS, no finding categories, and unknown-key verdict `rejected`.

**Failure modes and limits.** Palette and crossing remain deterministic sampled properties rather than caller-controlled exact axes. Future consumers needing them should add explicit axes and observation tests rather than infer control from seed search.

## D9 — Validate semantic ownership, not just syntax

**Choice.** `self_check` rejects malformed grids and semantic impostors: wrong dimensions, any input green, wrong blue/distractor counts, accidental extra pairs, shared endpoints, missing orientation, nonexclusive positives, multiple blocked pairs, invalid blockers, or blocked interiors lacking an untouched zero negative witness.

**Original rationale.** The baseline validator only required a nonempty rectangle, at least one blue, and no green, with texture-specific exceptions. That was insufficient to certify generated lessons.

**Alternatives considered.** (a) validate only generator-produced metadata; rejected because validators should establish properties from the grid. (b) accept a broad lawful-rule domain; rejected for `self_check`, which here represents the selected generator’s strict teaching profile. `rule_mirror` remains broad enough to execute the rule on arbitrary rectangular inputs.

**Probes.** Task tests include malformed grids and targeted semantic impostors. Final self-check/strict-profile, grammar, diversity, and distribution gates are green.

**Failure modes and limits.** `strict_canonical_like` intentionally equals the strict generator-domain check, not the complete mathematical domain of the Racket rule.

## D10 — Declare and test finite rivals explicitly

**Choice.** Declare `only_color_5_blocks` as the canonical shortcut and semantic rival, plus lesson competitors `connect_through_blockers`, `horizontal_only`, `vertical_only`, and `identity`. Set `EXAMPLES_NEEDED = 3` and implement `lesson_identifiable` against the actual declarations.

**Original rationale.** No semantic contract existed in the baseline.

**Alternatives considered.** (a) rely on labels alone; rejected because correct pair labels do not establish that demonstrations distinguish the intended rule. (b) hard-code rival names only in a probe; rejected because probes would drift from production declarations. (c) claim universal uniqueness; rejected as unsupported.

**Probes.** Tests prove the canonical shortcut fits 5/5 canonical pairs and that every generated example refutes every declared competitor. The reusable probe iterates declarations dynamically. The shared Racket-backed census reports 0 ambiguity for every named rival across 300 lessons and all 1,200 query rotations.

**Failure modes and limits.** This is finite hypothesis testing. Undeclared rivals remain unknown, and zero observed ambiguity is not a proof of universal induction.

## D11 — Synchronize authority text without changing semantics

**Choice.** Copy the authoritative `raw_code` exactly into the duplicated `target_code` field in the base authority JSON. Preserve rule hash `5074f7d7c8b5` and all executable behavior.

**Original rationale.** The two fields represented the same algorithm, but `target_code` alone contained two explanatory comments. No evidence indicated a semantic fork.

**Alternatives considered.** (a) change `raw_code` to include the comments; semantically harmless, but the selected canonical executable source already matched `raw_code`. (b) leave divergence; rejected because exact authority synchronization is a required gate. (c) modify the Racket algorithm; rejected because the generator, not the authority semantics, was defective.

**Probes.** Final authority sync reports one exact, whitespace-normalized, and comment-stripped group with execution parity PASS. Rule smoke and Racket lint are green. The authority JSON file SHA-256 is `79bf406bae82faf81cf71e2cfff3c80d5e355c04e90817f03cd525ef6a675e24`.

**Failure modes and limits.** This was a textual synchronization only. The review does not claim a new or corrected reference rule.

## D12 — Preserve failures and build reusable evidence

**Choice.** Retain the before battery, the intermediate dead-band failure, exact shortcut witness, 44-test portable runtime result, 300-lesson census, post-repair solve, and both adversarial audit witnesses. Add `workspace/probe_semantics.py` rather than only describing the reasoning.

**Original rationale.** The packet explicitly asks for reproducible evidence and tools that future agents can rerun.

**Alternatives considered.** (a) keep only final green logs; rejected because it erases causal evidence. (b) place one-off logic in top-level reports; rejected because executable probes are less ambiguous. (c) alter shared tooling during a task-local repair; rejected to keep the source delta within assignment scope.

**Probes.** Packaging and the fresh-packet replay bind the final source patch. Exact commands, working directories, exit codes, and evidence paths are in `RESULTS.json`.

**Failure modes and limits.** Large shared check runtimes are snapshotted and may be bundled by the return builder. Maintainer acceptance still treats these as reviewer-reported until replayed.
