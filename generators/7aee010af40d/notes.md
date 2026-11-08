# Working notes: 7aee010af40d

## 2026-10-07 review

The immutable 3.0.0 baseline passed all twelve standard battery stages, but complete lessons had a cross-example leak: `EXAMPLES_NEEDED == 5` and the target schedule also had period five, so the query at offset `+5` always repeated demonstration 0’s normalized answer. A source-bound probe measured 600/600 copies with zero lesson-hook failures.

Version 3.2.0 replaces that cycle with ten target roles, advances target room and finite-shape selection with absolute sample position, and supplies a reusable leakage probe under `workspace/`. The same 600-lesson plan now has zero query/output copies against any demonstration.

Semantic declarations were tightened. Shape/size coverage predicates are no longer presented as rule witnesses. The selected generator declares and enforces three executable competitors—smallest nonzero component, largest orange component, and first/top-left orange component—with corresponding counterexample witnesses. `first_orange` is explicitly recorded as a shortcut fitting all five canonical pairs.

Focused tests cover canonical parity, every query holdout in a six-pair bundle, the exact false-warning seed/start, executable witness/rival mappings, output-copy leakage, exact overrides, determinism and global RNG purity, structural impostors, and a distribution-invalid but oracle-executable recombination. Canonical data is loaded through public portable helpers.

Final evidence: 12/12 after-battery stages green; 22/22 selected tests; 300/300 production lessons and 1,800/1,800 rotations unambiguous against declared rivals. Limits: finite declared-rival evidence is not universal identifiability, and exact-output collision checks need task-specific interpretation for low-cardinality tasks.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b60d770a4531812fd6d5dbdc40d81cd9788370ae9733c6a6cac0d931e05dc2c6`.

# Decisions for `7aee010af40d`

## Scope and authority

- **Selected scope:** only `repo/generators/7aee010af40d/` was changed. The two audit targets were read-only.
- **Rule authority:** unchanged. The canonical Racket rule and `RULE_HASH = 8e254e2caadf` already expressed the intended transformation; the defect was in lesson distribution and semantic evidence, not the oracle.
- **Baseline used:** the immutable packet baseline, generator SHA `c53f91a142f71300e8bcbc6c6316cdd3615f18cd75fdfab44adf2812467abbc4`. Prior associated notes were treated as leads, not measurements.
- **Success criterion:** preserve per-grid lawfulness and canonical support while making complete five-demo lessons nontrivial, rejecting declared plausible shortcuts, surviving arbitrary query holdouts, and remaining deterministic/portable.

## Input and schedule choices

| Choice | Original rationale | Alternatives considered | Probe or evidence | Failure mode / limitation |
|---|---|---|---|---|
| `grid_h`, `grid_w` | Canonical-linked draws use one of the five canonical dimensions; broader draws use band-specific larger dimensions. This supplies canonical support plus spatial variation. | Make all draws canonical-sized; use wholly random dimensions. | Strict/profile gates and exact override tests in `checks/after/`; `test_override_boundaries_are_exact_in_every_band`. | Larger grids can change surface statistics without adding a new logical branch. The profile gate, not dimension variety alone, establishes canonical contact. |
| `small_k` | Target orange size spans 2–6. Sizes 2–3 support canonical profiles; 4–6 broaden cropped shapes. | Random size independent of schedule; retain the old five-slot size cycle. | Strict fraction 223/600 and all profile floors green; schedule tests cover exact bounds. | Size alone can become a shortcut if correlated with position or lesson order; the ten-role schedule and rival checks reduce, but cannot rule out every correlation. |
| `n_big` | Keep two or three larger orange competitors so the smallest-orange rule is executable and nontrivial. | Always two; unconstrained number of orange objects. | `self_check`, override battery, and structural-impostor tests. | More components do not by themselves teach “smallest orange”; first/largest/smallest-nonzero rivals still require explicit counterexamples. |
| `n_distractors` | Canonical-linked draws use one non-orange object; broader draws use two. Every demo includes a non-orange object smaller than the target. | Permit zero distractors; randomize count independently. | `smaller_nonorange_decoy` fires 600/600 in final semantic census and refutes `smallest_nonzero`. | Requiring this in every demo is intentionally stronger than the canonical data. It teaches color relevance but narrows the generated domain. |
| `distractor_color` | Draw from nonzero, non-orange colors `(1,2,3,4,5,6,9)` to avoid a fixed distractor color shortcut. | Fixed canonical palette; include cyan `8`. | Lint palette coverage and override tests. | Numeric color-rank shortcuts beyond the declared rivals remain possible in principle; this review did not enumerate all color formulas. |
| Ten target roles | Five demos followed by a query means a period-five target schedule leaks the answer. Ten roles make positions `i` and `i+5` deliberately different while preserving canonical-size frequency. | Random rejection until query differs; six-role schedule; retain five roles and change only the query. | Baseline/current leak probe: 600/600 versus 0/600 exact copies; full battery and 300-lesson census. | This is ordered curriculum logic. A universal “no repeated output” rule would false-positive on constant-output and naturally low-cardinality tasks. |
| Target room uses absolute `sample_index` | Advancing by five must also change spatial role, preventing first-demo location copying and supplying `first_orange` counterexamples. | Seed-only room assignment; random room shuffle. | `target_not_first_orange` fires 441/600; canonical shortcut is refuted; six-way holdout tests pass. | The finite room system is periodic. The census covers sampled starts and all holdouts inside each materialized bundle, not every possible long-range correlation. |
| Bent-shape selector uses seed plus absolute index | The first ten-role draft passed anti-copy tests but reduced output diversity. Traversing the full finite bent vocabulary restored diversity without giving up the schedule invariant. | Fixed prototypes for every role; unrestricted random shape. | `checks/lint-initial/result.json` captured the failure; final lint and diversity stages are green. | Shape vocabulary is finite, and duplicate outputs remain natural in this low-cardinality task. The repair targets deterministic query/demo copying, not all repetition. |

## Semantic contract

The baseline declared six `SEMANTIC_WITNESSES`, but four were only shape/size coverage predicates. A semantic witness should identify a concrete wrong rule and demonstrate disagreement with the oracle. I therefore separated curriculum diversity from executable rival evidence.

Declared rivals:

1. `smallest_nonzero`: choose the smallest connected nonzero component, ignoring color.
2. `largest_orange`: choose the largest orange component.
3. `first_orange`: choose the row-major first orange component.

Named witnesses:

1. `smaller_nonorange_decoy` refutes `smallest_nonzero`.
2. `target_not_largest_orange` refutes `largest_orange`.
3. `target_not_first_orange` refutes `first_orange`.

`first_orange` was also declared in `CANONICAL_SHORTCUTS`, because it fits all five usable canonical pairs. `lesson_identifiable` now checks every demo output and rejects a lesson whenever any declared competitor fits every demonstration. It does not require arbitrary shape categories or a fixed count of distinct rooms; those are distribution observations, not semantic necessities.

The exact false-warning regression uses hard seed `3012422862`, start `26`. It showed that a lesson can refute every named rival even when randomized placement repeats a room. The room-count condition was removed after its failing test was observed.

## Test strategy and failed attempts retained

- The answer-copy regression was written against the baseline and failed because two scheduled discoveries were reported; after the schedule repair it passes. Evidence: `checks/task-tests-red/result.json` and `checks/task-tests/result.json`.
- The semantic-contract tests initially failed because executable rivals and rival mappings were absent. Evidence: `checks/task-tests-semantic-red/result.json`.
- The first anti-copy schedule tripped output-diversity lint. Instead of weakening lint, shape selection was broadened. Evidence: `checks/lint-initial/result.json`.
- The first semantic hook revision falsely rejected one source-bound lesson for insufficient room-count variation. The exact case was frozen as a regression before removing that condition. Evidence: `checks/task-tests-position-red/result.json`.
- The selected-task tests originally used a brittle parent-depth path to canonical data. Public portable helpers replaced it; final explicit task tests pass 22/22.

## Reusable tool

`repo/generators/7aee010af40d/workspace/probe_lesson_output_leak.py` materializes consecutive five-demo lessons from any specified generator source, computes normalized output hashes, reports query equality with the first demo and with any demo, and reruns the task lesson hook. It can compare the frozen baseline and selected implementation and can fail CI with `--fail-on-finding`.

This tool intentionally reports rather than universally condemns repeated outputs. The suggested shared gate in `FEEDBACK_TO_CODEX.md` adds a collision-aware threshold and task-specific waiver.

## Verification boundaries

- The 12-stage battery and task tests establish consistency with the selected canonical authority and declared contracts, not training admission.
- The 300-lesson census checks 1,800 unique sampled inputs and 1,800 hold-one-out rotations against declared rivals. It is finite evidence, not a proof against unknown hypotheses.
- Audit counts refer to the exact source hashes and sample plans recorded in `AUDIT.md`; audit targets were not repaired.
- The post-repair solve is an exposed reviewer solve because generator work preceded it. It is not presented as blind.
