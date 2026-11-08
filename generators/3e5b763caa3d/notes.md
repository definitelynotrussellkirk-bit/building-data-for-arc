# Working notes: 3e5b763caa3d

Version 2.0.0 replaces the imported generator's ambiguous apparent-divider grammar with a strict canonical contract: one uniform nonzero divider, source cells only on its left, and a blank right side. The four-example teaching schedule varies both divider position and divider color so the canonical-fitting `grid_center_axis` and `fixed_gray_axis` shortcuts are refuted before the query.

The original 1.2.1 source is retained in `workspace/generator_v1.2.1_baseline.py`. Detailed measurements, counterexamples, decisions, and limitations are in the assignment-level review return.
## Current reviewer considerations

Source SHA-256: `e375d828b5a1fece2b1a43bf50f2059aa9366eb3bf7b158aa8e55e9a81ed074e`.

# DECISIONS — `3e5b763caa3d`

## D1: Preserve the canonical Racket authority

**Decision.** Keep the selected Racket rule unchanged and pin `RULE_HASH = "da67ea740136"` in the generator.

**Evidence and rationale.** All five canonical pairs are internally consistent, and the baseline defect was in generated inputs: its apparent divider could be non-uniform, causing the already-defined rule to take its geometric-center fallback. Changing the authority would have hidden that generator bug and invalidated canonical provenance.

**Rejected alternative.** Reinterpret “first full non-background column” as the authority and edit Racket accordingly. Rejected because the assignment's canonical outputs and rule hash already define a uniform-divider contract, while the baseline implementation did not satisfy it.

**Probe.** `checks/baseline-semantic-drift/counterexample.json` binds a baseline input, Racket output, and the 10-cell disagreement with the apparent-divider interpretation.

## D2: Replace, rather than incrementally patch, the imported grammar

**Decision.** Rewrite the 1.2.1 generator as a compact 2.0.0 grammar and retain the original source in `workspace/generator_v1.2.1_baseline.py`.

**Original rationale.** Unknown. The imported notes do not explain why it exposed dead palette/texture axes, allowed negative fixtures in the ordinary domain, or painted divider cells independently.

**Rationale.** The failures were coupled: semantic preconditions, exact controls, validation, profile support, and lesson identifiability were all wrong or absent. An incremental patch would preserve a misleading public surface and make it harder to prove which controls were lawful.

**Rejected alternative.** Keep every historical axis and add compatibility shims. Rejected because an advertised exact axis must be observable; dead controls are worse than a smaller honest contract.

## D3: Use six exact, independently observable axes

**Decision.** Expose only:

- `grid_h`: 7, 8, 9
- `grid_w`: 7, 9, 11
- `axis_mode`: left, center, right
- `divider_color`: 1, 5, 9
- `cells`: 6, 9, 12
- `n_distinct_colors`: 4, 5, 6

Unknown keys, boolean-as-integer values, and out-of-domain values raise an error. There are no undeclared incompatible combinations.

**Distribution rationale.** Heights 7–9 and widths 7/9 reproduce canonical shape profiles while width 11 gives lawful extra horizontal room. Three axis positions directly test structural rather than center-based inference. Divider colors include canonical gray and two non-gray values. Cell counts distinguish difficulty without altering the rule. Four to six source colors reproduce canonical palette sizes after adding background and divider.

**Failure modes considered.** Very dense left halves could accidentally create another uniform full-height nonzero column; generation reserves structure and `self_check` verifies uniqueness. A divider too near an edge could make reflections leave the grid; each axis mode is chosen from legal columns for the requested width.

**Rejected alternatives.** Continuous broad ranges were rejected because many combinations were either unsupported by the historical implementation or hard to make exactly observable. A free-form `palette_kind` or `texture` was rejected because those controls were previously dead and did not teach the rule.

## D4: Make canonical-profile support the default, not a rare accident

**Decision.** Cycle the five official `(height, width, palette-size)` profiles:
`(7,7,7)`, `(9,7,8)`, `(8,7,6)`, `(7,9,8)`, and `(9,9,7)`.

**Rationale.** The baseline hit 0/60 exact profiles and only 4/60 profile envelopes, despite the task being small enough to support exact coverage deterministically. Cycling profiles gives every band all five profiles in each 20-draw check and avoids relying on low-probability random matches.

**Rejected alternative.** Merely widen random ranges until occasional canonical profiles appear. Rejected because profile coverage would remain seed-sensitive and could regress silently.

## D5: Use a period-four semantic teaching schedule

**Decision.** Set `EXAMPLES_NEEDED = 4` and cycle:

1. left, gray divider;
2. center, non-gray divider;
3. right, non-gray divider;
4. left, non-gray divider.

The next generated pair is the query in production, while census testing also rotates every pair into the query role.

**Rationale.** All canonical pairs are compatible with two plausible shortcuts: use the geometric center, or use gray as the axis. Any four consecutive demonstrations include both an off-center and a non-gray witness, so neither shortcut reaches the query unchallenged. Four examples are enough to cover these branches without bloating each lesson.

**Rejected alternatives.** A random schedule was rejected because unlucky windows could omit a required branch. Center-only or gray-only curricula were rejected because they preserve the exact canonical shortcuts. Two or three demonstrations were not selected because they cannot guarantee all four schedule residues for every start.

**Limits.** The schedule refutes only declared competitors. It does not prove the task is uniquely identifiable against every possible hypothesis.

## D6: Treat structural legality as part of the data contract

**Decision.** `self_check` and `strict_canonical_like` require a rectangular grid, exactly one uniform nonzero full-height divider, nonzero source cells only to its left, a blank right side, and in-bounds reflected coordinates.

**Rationale.** Correct Racket labels are not enough if the generator's intended explanation points to a different feature. These checks make the input preconditions that select the rule explicit and reject the exact baseline failure.

**Rejected alternative.** Permit partial dividers, right-side content, or full-one-color “negative textures” in ordinary generation. Rejected because they are not lawful variants of this task and can invoke fallback behavior or create multiple explanations.

## D7: Add an independent oracle and executable competitors

**Decision.** Implement `rule_mirror` independently of Racket for task-local assertions, while retaining Racket as label authority. Encode `grid_center_axis` and `fixed_gray_axis` as executable competitors and bind them to named witnesses.

**Rationale.** A Python mirror catches generator/description drift cheaply, while Racket comparison protects against a shared implementation mistake. Executable rivals turn vague shortcut concerns into reproducible lesson-level claims.

**Rejected alternative.** Describe shortcuts only in prose. Rejected because prose cannot be scored over demonstrations, queries, or query rotations.

## D8: Make the repair portable and replayable

**Decision.** Add eight task-local tests using `reviewer_support.find_root` and `canonical_pairs`, retain the baseline source and exact counterexample, run the full battery, and run a 100-lessons-per-band rotated census.

**Rationale.** The first portable task-test attempt exposed brittle path assumptions; the final test uses the repository's supported helpers and passes in the isolated runtime. The larger census checks actual assembled lessons rather than inferring teachability from individual valid pairs.

**Limits.** The census samples 300 lessons and two declared rivals. It is strong regression evidence, not a universal proof.
