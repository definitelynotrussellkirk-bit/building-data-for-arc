# Segmented gravity generator implementation plan

> For agentic workers: use superpowers:executing-plans for implementation; independent reasoning and final review are delegated without filesystem access.

**Goal:** Replace an acceptance-only, control-ignoring sampler with a source-bound teaching generator for the unchanged downward, order-preserving, cyan-walled column rule.

**Architecture:** Keep all implementation and tests inside generators/866b956f2402. Separate input generation, teaching validation, and pure finite rivals within generator.py. Use the public Racket apply/check/census tools for labels and evidence. A period-three anchor/A/B schedule, with five demonstrations and one query, repeats each profile twice. Seed-only feature allocation makes A and B complementary for wall-free occupied columns, color 1, more than two walls, more than three occupied columns, and more than two pebbles in a segment.

**Tech stack:** Python 3.12+, supplied keyed RNG helpers, pytest, canonical Racket 8.10.

**Spec:** WORK/DUTIES.md, WORK/RETURN-GUIDE.md, repo/docs/SEMANTIC_GATE_CONTRACT.md, and the five canonical pairs retained in checks/main-authoring-view.log.

## Global constraints

Only selected-task source files may change. RULE_HASH must match 7cf1bdb14040. No canonical or Racket changes. Reject unknown controls and bool/float/string integer coercion. Teaching-domain rejection does not imply an undefined Racket transformation. Retain every actual failing check and bind final evidence to final source bytes. Private solve correctness remains unknown.

## Review focus

- Wall-free columns and bottom tails must move under the same rule.
- Color 1 must be an ordinary pebble, while 8 alone stops motion.
- Empty/consecutive/boundary-wall segments must preserve their walls.
- Multi-pebble order and dense inputs must not introduce sorting or object-gravity shortcuts.
- Profile mixtures must survive every single-pair holdout against the named finite bank; agreeing rivals remain survivors, not uniqueness proof.

## Task 1: Honest controls and useful teaching validation

- [ ] Add tests/test_generator_review.py for malformed grids, no-op teaching inputs, strict integer bounds, removed ignored controls, canonical acceptance, and generated wall-free/tail/color-1 witnesses.
- [ ] Run public task_tests on untouched v1.1.1 and preserve the expected failures.
- [ ] Implement v2 generator with exact grid_h 8..24, grid_w 7..24 and texture canonical|contrast. Remove the formerly ignored palette/count/density aliases. Keep named negative fixtures outside the ordinary texture domain.
- [ ] Run focused tests; fix real failures with separate evidence paths.

## Task 2: Executable semantic and lesson evidence

- [ ] Implement strict_canonical_like, pure semantic rivals, witness mappings, five-demo lesson_identifiable, schedule_profile and LESSON_SCHEDULE_PERIOD=3.
- [ ] Retain minimal input/Racket-output/rival-output fixtures, including a four-pair unique-profile holdout counterexample and its six-pair closure.
- [ ] Run public before/after batteries and explicit task_tests. Run a source-bound census with 100 lessons per band, five demos, one query, required query rotations, and an independent fixed-seed enumeration of all three starts.
- [ ] Inspect the generator and test evidence independently; preserve finite-bank and support limitations.

## Task 3: Complete the assigned review

- [ ] Finish the final-source visible-only solve with earlier exposure declared.
- [ ] Draw the two audit targets once after generator work; retain public Racket findings and no target edits.
- [ ] Complete REVIEW, DECISIONS, QUESTION_ANSWER, FEEDBACK_TO_CODEX and RESULTS.
- [ ] Apply the exact returned patch to a fresh original ZIP extraction, verify selected-file equality and rerun focused tests in its own runtime.
- [ ] Build and deliver only the official delta ZIP, including reproducible tools and evidence.

## Evidence-driven revision

The v2 twelve-stage battery passed, but the 300-lesson census found one production ambiguity and six holdout ambiguities against interior_columns_only. An independently implemented rigid-horizontal-run rival fit all five canonical pairs and produced singleton errors in seven of twelve diagnostic lessons. Thirteen new regressions failed before the fix. v2.1 adds a repeated anchor containing two adjacent same-color pebbles with different stopping heights and a moving boundary column, and declares the rigid rival. This is a deliberate construction restriction in one-third of default draws; the complementary contrast branches retain broader random placements. Full final-source checks remain required.


## Independent-review follow-up: adaptive sorting

Source review proposed choosing a separate sort direction from each segment's first two pebbles. Independent rescoring of v2.1.0's retained Racket labels found 107 singleton-error lessons out of 300, including 18 production-query ambiguities. Six exact lessons (two per band) were frozen, and all six regressions plus the missing-rival assertion failed before the repair (7 failed / 86 passed). Version 2.2.0 adds the rival and gives both long-stack profile copies a mixed-order prefix [a,c,b] with a<b<c. Canonical anchors retain their two-pebble structure. Racket is unchanged. All final-source validation must be rerun and separately source-bound.
