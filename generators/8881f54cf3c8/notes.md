# Working notes: 8881f54cf3c8

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.

## Review assignment

- Assignment: `review-4ad4d70cba3eb50c`.
- Imported generator: version `2.0.0`, SHA-256
  `bd8ced009c7db1f8fdfbde2fd0385dc3a530ba14b1b3eabdef6e4cfe8ff58f2d`.
- Final generator: version `2.1.0`, SHA-256
  `08f925892b5a1f39d9b8312899ae1a20c90ce98346ea1b9f5b58aa76e2653eb7`.
- Rule pin remains `d4cbbd7307ee`; authority semantics were not changed.

## Reproduced gaps

1. The original operation schedule ignored seed and difficulty. Production
   lessons always used demo operations `1,2,3,4` and operation 1 for the query.
   The standard battery was 12/12 green, so this was an episode-assembly blind
   spot rather than an existing gate failure.
2. The strongest natural canonical-fitting rival was undeclared: treat key 4 as
   XOR instead of A-minus-B. It fits all four canonical pairs because canonical
   B is a subset of A. The imported `CANONICAL_SHORTCUTS` entry
   `clean_boolean_excludes_key` fit only 3/4 canonical pairs.

## Selected repair

- Deterministically shuffle the four-operation cycle per seed and difficulty
  using `stable_rng`, retaining complete coverage in every four consecutive
  draws.
- Add executable rival `op4_xor_instead_of_a_minus_b` to canonical shortcut,
  semantic rival, lesson competitor, and A-minus-B witness contracts.
- Add source-bound tests under `tests/` and retain a standalone production-
  episode/branch-alias probe in `workspace/`.

## Verification

- Baseline battery: 12/12 green (`checks/before-complete/`).
- New tests against baseline copy: 5 failed, 17 passed as expected.
- New tests against final source: 22 passed.
- Source-bound task-test stage: 22 passed.
- Final battery: 12/12 green (`checks/after/`).
- Lesson census: 300 lessons, 1,500 pairs, 1,497 unique inputs, 0 ambiguous;
  every declared rival refuted in all 100 lessons per band.
- Post-repair visible-only solve: one revision, 4/4 visible demonstrations;
  earlier exposure yes, reference consultation during solve no.

## Known limitation

Because the schedule remains period 4 and a production episode uses four demos
then the next sample as query, the query operation still equals demo position 0.
The operation and full order now vary across episodes. Removing the positional
relation requires a broader lesson-assembly/schedule design change.
## Current reviewer considerations

Source SHA-256: `08f925892b5a1f39d9b8312899ae1a20c90ce98346ea1b9f5b58aa76e2653eb7`.

# Decisions: 8881f54cf3c8

## D1 — Preserve the selected authority, including the op-3 key asymmetry

**Input/evidence.** The selected rule pin is `d4cbbd7307ee`. It defines A as
color-2 cells excluding the top-left key, but B as every color-3 cell; therefore
a key value of 3 participates in B. The canonical third pair and the existing
`op3_key_contaminated_xor_branch` witness exercise this behavior.

**Decision.** Do not “clean up” the asymmetry. Keep the Racket rule, canonical
ledger, `RULE_HASH`, and Python mirror semantics unchanged.

**Rejected alternative.** Exclude the key from both motifs because that is the
more aesthetically natural Boolean-shape rule. That would change the selected
authority and fail canonical pair 3.

**Probe/failure mode.** The final semantic gate continues to verify the clean-
Boolean rival is refuted. A future source edit that drops key participation
should fail the task tests and semantic witness.

## D2 — Repair episode diversity with a seed-permuted four-cycle

**Input/evidence.** The baseline schedule ignored seed/difficulty and returned
`1,2,3,4` forever. Production always starts an episode at index 0, so the query
at index 4 was always key 1. `checks/shortcut-probe/before.json` reproduces this
for seeds 0–63 in every band.

**Decision.** Shuffle `(1,2,3,4)` deterministically using `stable_rng`, keyed by
seed, task, difficulty band, and generator version. Continue indexing the cycle
with `sample_index % 4`.

**Why this option.** It is the smallest change that preserves complete branch
coverage in every consecutive four-sample demonstration block, deterministic
replay, exact override behavior, and existing lesson-size assumptions. It also
makes production query operations and demonstration order vary across episodes.

**Rejected alternatives.** Independent random operation draws could omit a
branch from the four demonstrations. A global phase offset changes which fixed
operation is queried but still collapses across seeds. A period-5 schedule or
query-specific shift could break the shared expectation that every consecutive
four-demo lesson contains all four branches. Changing the shared lesson runner
was out of selected-task scope.

**Known limitation.** Any period-4 branch-complete cycle repeats at index 4, so
the query operation remains equal to demo position 0. The task-local probe emits
this as a warning rather than hiding it.

## D3 — Replace the invalid canonical-shortcut declaration with the true alias

**Input/evidence.** Exhaustive testing of all 12 single-key operation
substitutions against the four canonical pairs found exactly the natural key-4
alias: use XOR when the key is 4. It fits 4/4 because canonical B is a subset of
A. The prior `clean_boolean_excludes_key` entry fit only 3/4 and therefore was
not a canonical shortcut, although it remains a valid ordinary semantic rival.

**Decision.** Declare `op4_xor_instead_of_a_minus_b` in
`CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`; attach it to
`a_minus_b_branch`. Keep `clean_boolean_excludes_key` in the general rival sets
and op-3 witness, but remove it from `CANONICAL_SHORTCUTS`.

**Rejected alternatives.** Keep the old declaration for historical intent, or
add the new rival only to prose. Both would leave the executable contract
misleading and allow future gates to miss the actual canonical ambiguity.

**Probe/failure mode.** The task-local probe now fails if any declared canonical
shortcut does not fit every usable canonical pair, if a discovered branch alias
is undeclared, or if no generated counterexample is found.

## D4 — Reuse the existing partial-overlap distribution instead of adding a new profile

**Input/evidence.** Ordinary generated motifs already have exact partial overlap
and require both A-only and B-only cells. For key 4, B-only cells are the exact
witness separating XOR from A-minus-B. The final probe finds a seed-0 witness,
and the 300-lesson census refutes the alias in every lesson.

**Decision.** Do not add a special-case scene family. Add only the executable
rival and contract wiring.

**Rejected alternative.** Add canonical-shaped hand-authored key-4 examples.
That would increase code and distribution complexity without improving the
existing witness guarantee.

**Failure mode.** A future motif change that allows only B⊆A for key 4 could let
the alias survive. The regression tests, semantic witness, and lesson census
are intended to make that loud.

## D5 — Add source-bound tests under `tests/`

**Input/evidence.** The imported task had a root-level test file, but the
supported `task_tests` stage reported no tests because it discovers the selected
task’s `tests/` directory. This let the previous review rely entirely on other
gates.

**Decision.** Add `tests/test_generator.py` with schedule, declaration,
canonical-fit, generated-counterexample, determinism, override, and authority
mirror coverage. Write the regressions against the frozen baseline first, retain
the red log, then run the exact same tests against final source.

**Rejected alternative.** Modify the frozen root fixture or shared discovery.
The former would alter imported evidence; the latter is outside selected-task
scope.

## D6 — Keep a reusable probe and immutable baseline in task workspace

**Decision.** Retain the exact baseline source and a standalone episode/branch-
alias probe in `workspace/`. The probe uses public portable canonical helpers,
loads a supplied generator path, and writes JSON suitable for before/after or
future-agent comparisons.

**Reason.** The standard battery was green before and after. Without a focused
probe, the reason for the source change would be hard to reproduce and the same
episode-boundary blind spot could recur.

## D7 — Version and documentation

The observable sampling distribution and executable rival contract changed, so
`VERSION` is bumped from `2.0.0` to `2.1.0`. `RULE_HASH` is unchanged because
rule semantics are unchanged. `SUMMARY.md`, invariants, axis defaults, task
notes, and workspace instructions are updated to reflect the new behavior.

## Limits

The 64-seed episode probe is finite. The 300-lesson census is finite and checks
only declared rivals. The branch-alias search covers one-key substitutions, not
arbitrary programs. The task-local schedule fix does not alter the shared
runner’s query-position policy. No benchmark, model-training, hidden-query, or
approval gain is claimed.
