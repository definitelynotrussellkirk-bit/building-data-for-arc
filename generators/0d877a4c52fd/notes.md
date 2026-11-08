# Working notes: 0d877a4c52fd

## Selected repair (version 3.0.0)

The 2.0.1 baseline silently shortened failed placements, advertised dead or mismatched controls, lacked a canonical rule pin and semantic contract, never sampled an exact canonical profile, and accepted partial/ambiguous structures. It also inherited a teaching gap from the five canonical pairs: every rectangle had both spans at least two, so a `spaced_only` solver fit all examples.

The selected generator now constructs the full requested set or fails, validates the complete per-color corner grammar, exposes six observable exact axes, pins `RULE_HASH`, retains 50% 9×9 default support while covering every declared dimension, and schedules adjacent/spaced/mixed cases. The named-rival contract uses three demonstrations; the retained 300-lesson census checks every query rotation. See `workspace/probe_shortcuts.py` for the exact canonical-perfect shortcut and authoritative adjacent-span witness.

Imported associated notes retain original evidence and timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `028c8cf9c9873fd8624563786e0d3fa086142869503ae4510627c9733cc9b621`.

# Design decisions for `0d877a4c52fd`

## D1. Preserve the selected Racket authority

**Decision.** Keep the canonical Racket program unchanged and pin its normalized hash as `RULE_HASH = "bf8c9dd4f7fa"`.

**Reason.** The authority reproduced all five canonical outputs and correctly handled the new adjacent-span witness. The defects were in generator support, validation, controls, and teaching evidence, not in the transformation.

**Rejected alternative.** Rewriting the rule to enforce a minimum side span would have encoded the canonical shortcut as the task and contradicted the authority's valid behavior on adjacent rectangles.

**Evidence.** `checks/shortcut-witness.json`; `checks/after/checks/0d877a4c52fd_after_battery_summary.json`.

## D2. Define one complete, auditable input grammar

**Decision.** A lawful input has a 6–12 by 6–12 integer ARC grid, zero background, exactly two or three foreground colors, exactly three cells per color, exactly two occupied rows and columns per color, one blank implied corner, and disjoint four-corner sets across colors.

**Reason.** This is the smallest grammar that precisely captures the canonical transformation while making every generated sample structurally unambiguous. It allows adjacent and spaced rectangles without inventing distractors or extra operations.

**Rejected alternatives.** Allowing partial colors, four already-complete corners, collinear triples, shared implied corners, or unrelated foreground noise was rejected because the selected rule has no demonstrated policy for those cases. The validator now rejects them instead of letting malformed lessons pass.

**Failure modes.** The clean grammar does not establish behavior on noisy or overlapping extensions. Those remain explicitly outside generated support.

## D3. Construct the full requested sample or fail

**Decision.** Enumerate candidates for each requested span family, shuffle deterministically through `gen_ctx`, and backtrack over disjoint corner sets until all requested rectangles are placed.

**Reason.** The baseline's capped retry loop could return fewer rectangles than requested, making count controls and teaching claims unreliable. Full construction makes `n_rects` exact and removes a hidden fallback branch.

**Rejected alternatives.** Increasing the retry limit or adding another fallback would reduce but not eliminate silent shortening. Post-hoc accepting whatever was placed would preserve the defect.

**Probe.** `test_generated_samples_are_complete_lawful_and_collision_free` in `repo/generators/0d877a4c52fd/tests/test_generator_0d877a4c52fd.py`.

## D4. Advertise only controls recoverable from pixels

**Decision.** Replace inherited aliases and dead metadata with six axes: height, width, rectangle count, one of three disjoint palette bands, one missing-orientation family, and one span family.

**Reason.** Each value is directly recoverable by `observe_overrides`; exact override requests can therefore be audited without trusting generator metadata. Unknown keys, booleans masquerading as integers, floats, strings, and out-of-range values fail closed.

**Rejected alternatives.** Keeping compatibility aliases such as generic `texture`, `palette_size`, or unrelated anchor/asymmetry controls would preserve ambiguous or no-op API surface. Inferring palette family from overlapping color pools was rejected, so the three pools are disjoint.

**Evidence.** `checks/stage-override-3/result.json`; final task tests.

## D5. Balance canonical support with declared range coverage

**Decision.** Use a 12-position height/width schedule containing six exact 9×9 positions and one occurrence of every other declared size from 6 through 12. Cycle two and three rectangles and all three palette bands.

**Reason.** The strict profile floor needs ordinary canonical-like support, while the axis declaration must describe what ordinary sampling actually exercises. Fifty percent 9×9 support is strong enough for each band's 20-draw profile check without collapsing the distribution to one size.

**Rejected alternatives.** The first implementation sampled only 9×9. Although semantically valid, defect lint correctly rejected the unused 6–12 claims. Pure random dimensions were also rejected because a small profile-floor sample could miss 9×9 and because deterministic schedule coverage is easier to audit.

**Test-first evidence.** `checks/task-tests-red-axis-span/result.json` then `checks/stage-defect_lint-2/result.json`.

## D6. Teach the canonical-perfect span shortcut explicitly

**Decision.** Declare `spaced_only` as a canonical shortcut and schedule `adjacent`, `spaced`, and `mixed` span cases. Use three demonstrations and require `lesson_identifiable` to refute every named rival before accepting a lesson.

**Reason.** All five canonical pairs have both rectangle spans at least two, so a solver can fit them while ignoring adjacent-side rectangles. One adjacent witness changes the answer at a specific cell; mixed support also prevents the opposite `adjacent_only` shortcut.

**Rejected alternatives.** Unconstrained random span selection could produce three spaced demonstrations and reproduce the ambiguity. Two demonstrations provided less schedule slack across corner orientation, span family, color ownership, and multiple-object behavior. More than three was unnecessary after every sliding window and every census rotation passed.

**Evidence.** `QUESTION_ANSWER.md`; `checks/shortcut-witness.json`; `checks/lesson-census.json`.

## D7. Keep the Python rule as a test mirror, not authority

**Decision.** Implement `rule_mirror` from the same structural analysis used by validation, but use public `Catalog.apply` Racket receipts for authority claims.

**Reason.** The mirror gives fast deterministic labels for task-local tests and lesson rivals. Separately checking its exact witness and canonical pairs against Racket prevents a self-consistent Python implementation from becoming its own proof.

**Evidence.** `test_rule_hash_is_pinned_and_adjacent_witness_matches_authority`; `checks/shortcut-witness.json`.

## D8. Retain failures and build a reusable probe

**Decision.** Keep all meaningful red runs and add `workspace/probe_shortcuts.py`.

**Reason.** Future reviewers can reproduce the strongest shortcut, canonical fit count, exact authority-labelled witness, schedule support, and 72 teaching windows without reconstructing the analysis from prose.

**Failed attempts retained.** Initial 9/10 failures, the 9×9-only axis failure, the absent-probe failure, the first defect-lint failure, and the source-checkout import-path reproducer remain under `checks/`.

## Distribution limits

The selected sampler does not contain distractor colors, shared implied corners, multiple triples of one color, or malformed objects. Palette colors are chosen within one of three disjoint bands per grid. These restrictions make controls observable and examples clean, but finite rival and census results do not prove universal induction outside this grammar.
