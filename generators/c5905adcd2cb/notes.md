# Current notes: c5905adcd2cb

## Intended canonical rule

On the fixed 11×11 gray-5 lattice, scan row-major for the yellow-4 marker. Its quotient-by-four coordinates select the source 3×3 macro-cell; its local row and column select the destination macro-cell. Preserve gray, clear every other cell, then copy every nonzero/non-gray source cell—including the marker—to the same local offset in the destination.

## Current decisions and evidence

- Keep `VERSION = 3.0.0` and `RULE_HASH = 93e6c6c4b04f`. Valid generated inputs and the canonical transformation did not change.
- Reject non-literal `seed` values and reject non-literal or negative `sample_index` values before `gen_ctx`. The previous source accepted booleans, floats, and `sample_index=-1`; focused regression tests now cover the strict scalar contract.
- Keep archival `raw_code` unchanged, but make both selected base `target_code` fields byte-identical to the canonical program. Before repair they were execution-equivalent but whitespace-divergent.
- Use portable task tests through `reviewer_support.find_root`, `canonical_path`, and `load_selected_generator`; the former fixed-parent path failed in the copied task-test runtime.
- Declare an executable semantic contract. `drop_marker` tests the wrong hypothesis that yellow 4 is control metadata rather than copied payload. `preserve_distractors` tests the wrong hypothesis that copying does not require the global clear. Both witnesses are generated in every sampled band, and `lesson_identifiable` reports a rival that fits all demonstrations but changes the query.
- The prior associated note `GNOTE-000178` was used as a lead, not as current measurement. Its canonical rule summary remained correct; its claim that both selected authorities were exact was rechecked and narrowed to execution equivalence before this repair.

## Proposed parametric extension

`workspace/parametric/destination_decoder_episodes.py` is a separate authoring prototype. The canonical/default setting maps marker-local `(row,col)` directly to destination macro `(row,col)`; the alternative transposes it to `(col,row)`. Source selection, global clearing, copied payload, and local offsets remain invariant. The setting is fixed once per episode, all labels are executed by exact retained Racket, public challenges omit private metadata/query labels, and demonstrations are constrained to off-diagonal codes so the two declared settings are distinguishable.

This prototype does not modify the selected production rule, generator API, catalog, or approval state.

## Assumptions and limits

- The selected generator intentionally stays on the canonical 11×11 lattice; shape diversity would be distribution drift for this family.
- The semantic gate checks two declared plausible rivals, not all possible ARC programs, so finite identifiability is not a proof of unique induction.
- Public anchor profiles are exact official scenes; generalized profiles cover empty/light/dense destinations, same-source/destination, marker-only, and full-source boundaries.
- The first marker is authoritative for broad `rule_mirror` inputs, while calibrated generated inputs require exactly one marker.
- No Racket semantics were changed. Only selected authority text normalization and Python-side validation/semantic declarations changed.

## Current owner source and evidence limits

Accept literal scalar boundary,portable test roots and executable strictness/two witnesses/two rivals. VERSION3.0.0 and canonical Racket behavior unchanged;selected authority normalization statically verified. Reviewer reports12/12 battery,118 tests+5 subtests repeated fresh full96709-file replay,300 lessons/1200 rotations/1199 unique inputs clean,60/60 profile. Proposed direct/transpose destination decoding keeps11x11 lattice grammar;2 episodes with6 demos/4 queries identify settings and preserve private/public split. Finite declared rivals only;broader mirror first-marker convention remains distinct from exactly-one-marker generated domain. No variant/training approval. Owner checked hashes and public/private structure statically; tests and labels remain reviewer-reported.
## Current reviewer considerations

Source SHA-256: `5d9cebc09f84a2107cc85ebac93abcdad80804818eaec6f3f0a5c501c1b67cfa`.

# Decisions for c5905adcd2cb

## D1 — Preserve the canonical rule and generated distribution

**Choice.** Keep the 11×11 gray-lattice grammar, the existing public/general profile schedule, `VERSION = "3.0.0"`, and `RULE_HASH = "93e6c6c4b04f"`.

**Rationale.** The baseline canonical transformation, profile support, diversity, override handling, grammar, and exact Racket execution already passed. The measured defects were API validation, selected-authority text divergence, missing portable tests, and missing semantic teaching declarations—not a wrong transformation or underperforming sampler.

**Alternatives rejected.** I did not change canvas shape, add new production profiles, or alter destination/source semantics. Those changes would create distribution drift and would require a version/rule review unrelated to the reproduced failures.

**Probe and limit.** The final battery reports 60/60 profile-floor exact hits and 60/60 envelope hits, and the full battery is 12/12 green. Finite generated coverage is not a proof over every possible 11×11 lattice input.

## D2 — Fail closed on strict scalar arguments

**Choice.** Validate `seed` as a literal `int` (not `bool`) and validate `sample_index` as a nonnegative literal `int` before calling `gen_ctx`.

**Rationale.** Baseline `defect_lint` reproducibly accepted booleans, floats, and `sample_index=-1`. The generator API promises deterministic indexed sampling; accepting Python's bool-as-int coercion or negative indices makes replay metadata ambiguous.

**Alternatives rejected.** Coercing values with `int(...)` would hide caller errors. Validating only `-1`, the first observed warning, would leave the rest of the strict-scalar matrix broken.

**Probe and limit.** Focused tests cover invalid `seed`/`sample_index` values and valid controls; final `defect_lint` is green. This intentionally does not add validation for unrelated optional overrides already covered by the shared override gate.

## D3 — Synchronize selected authority text but preserve archival source

**Choice.** Make both selected `target_code` fields byte-identical to canonical `program_solution`; leave both archival `raw_code` fields untouched.

**Rationale.** Baseline authority sync showed two selected exact-text groups despite execution parity. The return guide distinguishes selected executable authority from historical raw source.

**Alternatives rejected.** Reformatting canonical authority or rewriting `raw_code` would erase provenance. Leaving whitespace-only selected divergence would continue to fail the exact authority contract.

**Probe and limit.** Final authority sync is green with execution parity. Its receipt explicitly reports `selected_synchronized_archival_divergent`; no Racket behavior changed.

## D4 — Declare the two highest-value semantic rivals

**Choice.** Add an executable semantic contract with `strict_canonical_like = self_check`, witnesses `marker_is_payload` and `global_clear`, and rivals `drop_marker` and `preserve_distractors`. Use the same two rivals in `LESSON_COMPETITORS` and require three demonstrations per lesson.

**Rationale.** The two common misreadings are that yellow 4 is metadata rather than copied payload and that the task copies a source pattern without globally clearing distractors. Each rival is simple, deterministic, agrees on some plausible inputs, and changes outputs on retained witnesses.

**Alternatives rejected.** A prose-only rule summary cannot be checked. An unbounded library of speculative rivals would make the gate costly and difficult to interpret. Generic shared mutations remain supplemental diagnostics.

**Probe and limit.** Final semantic evidence has 600/600 strict draws, both witnesses in every band, both rival claims verified, 12/12 three-demo/one-query production lessons identifiable, and 0/48 diagnostic rotation ambiguities. The larger required-rotation census has 300/300 lessons, 0/1,200 pair ambiguities, 0/1,200 rotation ambiguities, and 1,199 unique inputs. This is finite declared-rival evidence, not proof of unique induction over all programs.

## D5 — Make task tests portable

**Choice.** Resolve repository/runtime paths through `reviewer_support.find_root`, `canonical_path`, and `load_selected_generator` instead of a fixed `Path.parents[...]` depth.

**Rationale.** The original tests worked only in one repository layout and failed when copied into the task-local runtime used by the checker.

**Alternatives rejected.** Adding another guessed parent depth would merely move the failure. Importing private `puzzle_generators.per_puzzle` aliases would also couple tests to one layout.

**Probe and limit.** The isolated task-test stage passes 118 tests plus 5 subtests (123 total) in the copied runtime. The same pattern is recommended as shared feedback because audit target `1137ac565856` reproduces the old failure.

## D6 — Keep the parametric extension separate from production

**Choice.** Build a runnable authoring prototype in `workspace/parametric/` with episode-level parameter `destination_decoder ∈ {direct, transpose}`. `direct` is the canonical default `(row,col) → (row,col)`; `transpose` uses `(row,col) → (col,row)`. Source selection, global clear, copied payload, and local offsets remain invariant.

**Rationale.** This is the narrowest meaningful parameter that changes the rule rather than only surface texture. It directly exercises whether demonstrations identify an episode-fixed latent rule choice.

**Alternatives rejected.** Parameterizing colors, clutter density, or source shape would not change the core transformation. Merging the transpose setting into the approved production generator would silently redefine the task.

**Probe and limit.** Two retained episodes exercise both settings; six demonstrations identify the chosen setting, four queries are labelled by exact persistent Racket execution, and a shared off-diagonal witness produces distinct outputs. Program SHA-256 values are `6ef97f7ff71c1a4b9c33cdb311d13f8e0b00d7957437dd06935748a7705a7f05` (direct) and `91d39943c508dbbd01f39106d5f779382efc3094d1468e6fa69ac9aba5af3b65` (transpose). This remains a proposed prototype, not production approval.

## D7 — Treat lesson ordering as an explicit policy

**Choice.** For the repaired task, require identifiability under every held-out position in the retained lesson bundle, not only the production query position.

**Rationale.** The assigned question asks about data value for a small model, and the audit of `fa55db418c9d` demonstrates that ordered-production success can conceal a query-rotation shortcut. The repaired task's small period makes exhaustive held-out rotation cheap.

**Alternative retained for other tasks.** An intentionally ordered curriculum may use diagnostic-only rotations, but it must state that policy and must not claim arbitrary-query support.

**Probe and limit.** The 300-lesson census uses three demonstrations, one query, all four held-out positions, 100 deterministic seeds per difficulty band, and a required-rotation policy. Rotations reuse each materialized bundle; they do not enumerate every possible generated scene.

## D8 — Preserve honest solve and audit boundaries

The blind task was solved before opening repair internals and finished in one visible-only revision. The post-repair solve was generated from final generator bytes, finished in one revision, and declares earlier rule exposure `yes` and reference consultation during the solve `no`. Audit targets were inspected and evidenced but not modified, as required.
