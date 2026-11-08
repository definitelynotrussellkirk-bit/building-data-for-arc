# Working notes: f4d4fb4404c6

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `d5b9411d681caa2bbcb75b27254c86a6d14dfe78dc0225a40658f9b732345680`.

# Decisions for review `review-4c19836a7d49afd1`

## Evidence basis

The pinned baseline was SHA-256 `7f0f658cb66d3aef986723d30a3bd7aacacfc52300053fe31fab7022e1888b31`. I read the existing `notes.md`, current generator, canonical examples, focused tests, and review index. Prior return `review-f0f879d9b93ecdc8:v0001` and its approval receipt were used only as a lead; all conclusions below are based on commands run against the packet's pinned bytes. The baseline was already semantically strong, so the repair is deliberately narrower than the historical v3.1 redesign.

## R1 — Validate `difficulty` at the public boundary

**Choice.** Add one `_validate_difficulty` helper and call it from both `generate` and `schedule_profile`. Accept only `None`, `easy`, `medium`, and `hard`; reject booleans, numbers, containers, and unknown strings with `ValueError`.

**Original rationale.** The generator already treated only those four values as meaningful, but unknown values silently fell into the mixed band. The declared public contract and strict battery therefore disagreed with execution.

**Alternatives rejected.** Coercing strings or treating every unknown value as mixed would preserve ambiguity and mask caller errors. Validating only in `generate` would leave the public schedule helper inconsistent.

**Probe and failure modes.** The baseline `defect_lint` retained 15 invalid-difficulty acceptances across three band contexts. Focused tests cover six scalar/container types and both entry points. Valid calls for all four accepted values are checked for determinism and `self_check == []`.

**Limitation.** This does not add seed validation beyond the existing plain-integer check; it repairs only reproduced selected-task defects.

## R2 — Reject negative `sample_index` consistently

**Choice.** Require `type(sample_index) is int and sample_index >= 0` in `generate` and `schedule_profile`.

**Original rationale.** Sample indices identify forward curriculum positions. Negative values are outside the intended contract, yet `schedule_profile` mapped them to a valid profile through Python modulo and `generate` accepted them.

**Alternatives rejected.** Normalizing with `abs`, modulo, or offsetting would make invalid calls silently alias lawful samples. Validating only one entry point would preserve a split contract.

**Probe and failure modes.** The minimal counterexample is stored at `repo/generators/f4d4fb4404c6/counterexamples/review-4c19836a7d49afd1/strict-call-contract.json`; the regression calls both entry points. The intermediate after battery is retained because it showed this as the remaining strict-scalar defect after the first repair.

## Preserve version, sampling, and authority

**Choice.** Keep `VERSION = 3.1.0`, all four scene profiles, the deterministic schedule, dimensions, palettes, overrides, semantic rivals, and Racket authority unchanged. Correct the stale `schedule_profile` docstring from “three-profile” to “four-profile.”

**Rationale.** Lawful calls produce the same bytes as the approved baseline; the only production behavior change is rejecting previously invalid calls. A version bump would perturb `gen_ctx` randomness and unnecessarily change every valid sample. No evidence justified changing `RULE_HASH=052ea839cbdd` or canonical data.

**Probe.** The final battery binds the new file hash and is 12/12 green. Portable tests check valid-call determinism and lawfulness. The final 300-lesson census has zero declared-rival ambiguities in production and rotations.

## P1 — Choose `copy_limit` as the semantic parameter

**Choice.** Build a task-local proposed prototype with two episode-level settings: canonical `to_edge` and nearby `one_copy`. Choose one setting once per episode using seed parity; keep it fixed over three demonstrations and one query.

**Why this parameter.** It changes an executed semantic decision—how many translated copies a marker commands—while preserving the original objects, edge-marker relation, selected frame, direction, color ownership, four-cell translation, and clipping logic. The default is byte-exact canonical Racket.

**Alternatives rejected.** Varying frame size conflicts with the fixed four-cell reasoning structure. Varying stride changes both object geometry and translation law. Varying marker direction or frame color is an input-distribution parameter, not a hidden rule parameter. Adding collision resolution would require a new authority decision outside the current domain.

**Input choice.** Every prototype input has room for at least two translated copies, ensuring `to_edge` and `one_copy` disagree. Inputs are generated deterministically from the episode seed and are validated by the selected generator's `self_check`.

**Labeling and checks.** Live Racket execution is the authority for both settings; an independent Python reference only cross-checks. Public challenges omit parameter names, Racket text, and query outputs. All single-query rotations must contain at least one demonstration that refutes the alternate setting; the retained two episodes satisfy this for all 8/8 rotations.

**Limitations.** Only two settings and eight episode inputs were evaluated. The evidence refutes only the alternate `copy_limit` setting, avoids chain collisions, and does not grant production or training approval.

## Q1 — Retain multicolor frames as the canonical-shortcut discriminator

**Choice.** Keep `global_frame_color` as the strongest canonical-fitting shortcut and retain a deterministic `multicolor_frames` witness.

**Rationale.** All eight canonical pairs permit the incorrect hypothesis that one color should be used globally. The intended law copies each selected frame's own color. Independently colored frames are therefore the minimal semantic discriminator without changing geometry.

**Probe.** Seed 918, sample index 2, difficulty hard, and `scene_profile=multicolor_frames` emits the exact lawful input in `checks/question/input.json`. Live Racket and the Python mirror agree; the rival differs in 72 cells, first at row 0, column 15 (`6` intended versus `9` rival).

**Failure modes.** The witness checks the selected generator hash, rule hash, override observation, validator result, canonical-rival fit, and exact output disagreement. A shared-color scene would not be a valid discriminator.

## Loader and wrapper choices

**Choice.** Keep task-local loading and exact Racket wrapping inside the prototype/test workspace rather than patching shared packet code, which is outside the allowed delta.

**Rationale.** The public `puzzle_generators.rule_wrap.wrap_rule` imports `scripts.comment_solutions`, absent from the portable source runtime. The shared loader can also collide with an already imported source-tree `puzzle_generators` package in staged tests. The final task-local loader finds the selected source explicitly and the prototype's wrapper preserves exact program text.

**Limitation.** These are local compatibility measures; shared-tool improvements are proposed in `FEEDBACK_TO_CODEX.md`.

## Final solve and stopping decision

The post-repair solve was prepared from final SHA `d5b9411d…`. Because the rule had been seen during generator work, earlier exposure is honestly `yes`; no rule/reference source was consulted during the solve. One structural implementation passed all 3 visible demonstrations, so further revisions would have manufactured activity without new visible evidence. Private query correctness remains intentionally unknown.
