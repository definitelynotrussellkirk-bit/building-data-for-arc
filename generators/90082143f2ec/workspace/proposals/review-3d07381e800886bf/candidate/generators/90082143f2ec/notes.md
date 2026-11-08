# Working notes: 90082143f2ec

## Intended rule

For a noisy colored-band grid, compute each row mode and column mode, compare the
number of cells agreeing with those modes, and fill every line on the more
coherent axis with its mode.  The generator keeps all nine non-background colors,
3–5 contiguous bands, strict modal slices, and 13–21% visible noise.

## Current distribution decision — version 4.0.0

The prior `local-random-4828ff4f17c5` return introduced a deterministic four-slot
schedule matching the four canonical shapes.  That was useful for canonical
coverage, but it accidentally made height a perfect proxy for the answer axis:
height 13 was always vertical and height 15 always horizontal.  A learner could
therefore ignore coherence and still match every generated and canonical case.

Version 4.0.0 reverses that coupling with an eight-slot schedule.  Each canonical
shape occurs once with vertical bands and once with horizontal bands.  Match and
mismatch slots alternate so every ordinary three-demonstration window and every
three-of-four query rotation contains a counterexample to the height-only rival.
The schedule retains both noise levels and at least two band counts in every
three consecutive slots.  `shape_axis_shortcut` is now an executable declared
competitor with explicit short-horizontal and tall-vertical witnesses.

A retained Racket-labelled witness is in
`counterexamples/shape-axis-shortcut.json`.  The old rival differs from the
canonical rule on 134 cells of a valid 13×14 horizontal case.

## Authority and tests

The canonical Racket program and rule hash `a86d1f36d1d2` were not changed.
Both active task-local `target_code` fields were synchronized byte-for-byte to
that canonical source and marked `canonical_exact_sync`; archival `raw_code`
retains its original bytes. The previous active text was behaviorally equivalent
but failed exact selected-source provenance checks.

The focused tests now resolve canonical data through `reviewer_support` rather
than a fixed `__file__.parents[...]` depth, so they run in the portable task-test
runtime.  They cover all eight retained canonical labeled inputs, exact authority
sync, the eight schedule slots, every cyclic three-demo/query rotation, controls,
mutations, Racket execution, and a 600-draw semantic/stability census.

## Reviewer-reported candidate evidence

- Full after battery: 12/12 green, generator SHA-256
  `161d76e8534f32a379e801cd6cfd42462dcd40354f4a9dab2d3b04884993ef91`.
- Focused tests: 9/9 passed.
- Production census: 300/300 lessons materialized; zero ambiguous ordered lessons
  and zero ambiguous results across 1,200 query rotations.
- Exhaustive declared schedule at seed 0: 24/24 lessons and 96/96 rotations clean
  across all eight starts and all three difficulty bands.

## Known limits and open findings

Difficulty changes concrete colors, widths, and noise placement; it is not a
calibrated cognitive-complexity scale.  The finite rival set and finite census do
not prove uniqueness against every possible program.  Overrides can intentionally
leave the canonical four-shape schedule, though `self_check` and exact-observable
control tests still bind them to the teaching grammar.  No semantic change was
made to the Racket rule.

## Selected authority and archive preservation

Maintainer retained the original raw_code bytes in both task-local authority records, synchronizing only selected target_code with the unchanged canonical program. The returned full battery describes the reviewer candidate that rewrote both fields; it is not a new full-battery result for this archive-preserving variant. The focused authority regression checks the exact archived SHA-256 as well as the active canonical source. See evidence/authority-field-selection.json.
## Current reviewer considerations

Source SHA-256: `161d76e8534f32a379e801cd6cfd42462dcd40354f4a9dab2d3b04884993ef91`.

# Decisions for `90082143f2ec`

## D1 — Reverse the four-slot shape/orientation coupling

**Prior choice.** The retained lead from `local-random-4828ff4f17c5`
(`GNOTE-002174`) chose a deterministic four-slot schedule so every canonical
shape and nine-color profile appeared and each ordinary lesson contained both
orientations and noise levels.  That rationale was sound for canonical support
and fixed-axis rivals.

**Failure discovered.** Across all four slots, height 13 always meant vertical
bands and height 15 always meant horizontal bands.  The executable rival
`height_13_columns_else_rows` therefore matched every case in the old support.
`checks/shape-axis-shortcut-before.json` records all old schedule windows.  This
was distributional equivalence, not merely a single ambiguous query: the rival
never had to inspect coherence at all.

**New choice.** Keep the same four canonical shapes but use eight slots, pairing
each shape with each orientation:

1. 13×14 vertical, 3 bands, moderate noise
2. 13×14 horizontal, 4 bands, high noise
3. 15×14 horizontal, 5 bands, moderate noise
4. 15×14 vertical, 3 bands, high noise
5. 13×17 vertical, 4 bands, moderate noise
6. 13×17 horizontal, 5 bands, high noise
7. 15×15 horizontal, 3 bands, moderate noise
8. 15×15 vertical, 4 bands, high noise

Match and mismatch cases alternate.  Every three consecutive slots contain both
orientations and noise levels and at least two band counts.  More importantly,
every three-of-four holdout rotation contains an example where height predicts
the wrong axis.  `LESSON_SCHEDULE_PERIOD = 8` makes this contract enumerable.

**Why not randomize orientation independently?** Random orientation would break
the deterministic coupling in expectation but would permit unlucky three-demo
windows where the height shortcut survives.  The downstream lesson size is only
three demonstrations, so a constructive schedule is cheaper and stronger.

**Why not add noncanonical shapes?** Shapes outside the four linked canonical
profiles could also break height correlation, but they would weaken strict
canonical-profile coverage and introduce a second distribution change.  Pairing
existing shapes with both axes isolates the needed repair.

**Why not increase `EXAMPLES_NEEDED`?** More examples would raise cost and still
would not repair a support where every case obeyed the same shortcut.  Three
demonstrations are sufficient once the schedule is counterbalanced.

**Evidence.** The focused test enumerates all eight starts, all three difficulty
bands, and all four query positions.  `checks/schedule-census.json` independently
Racket-labels 24 lessons and 96 rotations.  `checks/lesson-census.json` checks 300
production lessons and 1,200 rotations.  All are clean against declared rivals.

## D2 — Promote the discovered shortcut to an executable semantic competitor

Added `shape_axis_shortcut` to `SEMANTIC_RIVALS`, `LESSON_COMPETITORS`, and
`CANONICAL_SHORTCUTS`, plus `vertical_on_tall_shape` and
`horizontal_on_short_shape` witnesses.  This prevents a future schedule edit
from silently restoring the same correlation.  The compact Racket-bound witness
is `repo/generators/90082143f2ec/counterexamples/shape-axis-shortcut.json`.

A prose warning alone was rejected because the previous semantic gate was green:
it could not detect a rival that was absent from the executable rival set.

## D3 — Preserve the canonical rule; synchronize active authority source

The canonical Racket program already produced the correct outputs and retained
rule hash `a86d1f36d1d2`.  No semantic rewrite was justified.  The two active
base-solution JSON records contained behaviorally equivalent but text-divergent
programs, causing exact provenance checks to fail.  Their `raw_code` and
`target_code` now equal the canonical `program_solution` exactly and their status
is `canonical_exact_sync`.

Keeping behaviorally equivalent variants was rejected because provenance is part
of the task contract: sampled parity cannot prove future parity, and the canonical
source already exists as the single authoritative text.

## D4 — Make focused tests portable rather than weakening preflight

The selected test used a fixed parent-depth guess and a legacy helper import,
which worked only in the original repository layout.  The portable task-test
runtime correctly rejected it before pytest.  The test now uses
`reviewer_support.find_root`, `canonical_path`, `canonical_pairs`, and
`normalize_grid`.

Disabling or bypassing the preflight was rejected.  The preflight diagnosed a
real portability defect and supplied the correct helper API.  The final test
covers all eight retained canonical labeled inputs, not only one deduplicated
variant.

## D5 — Keep difficulty semantic-neutral

Difficulty continues to alter concrete colors, run widths, and noise placement
through an independent construction RNG while preserving the same profile
schedule and rule.  This follows retained limitation `GNOTE-002179`: there is no
claim that hard examples require deeper reasoning.  Introducing an unvalidated
complexity ranking was outside this repair and could create another hidden
correlation.

## Limits

The tests and censuses cover a finite declared rival family, not all programs.
The exhaustive schedule claim is fixed to seed 0 and the declared eight-slot
period; the 300-lesson census supplies broader stochastic coverage but is also
finite.  Exact overrides can produce teaching-grammar cases outside the four
canonical shapes.  These are supported and observable, but the standard lesson
schedule remains canonical-shaped by design.

Maintainer portable task-test check: 9/9 passed on the archive-preserving variant, including the active-source and archived-hash assertions. This is a focused CPU check, not a full battery or model-learning measurement.

## 2026-10-23 — Proposed episode-fixed `axis_policy` extension

A task-local prototype now exposes one binary setting fixed for the whole episode:
`more_coherent` (the canonical default) or `less_coherent`.  The default returns
the exact canonical Racket program bytes.  The alternate computes the same row
modes, column modes, and coherence scores, then selects the lower-coherence axis;
the production generator, canonical ledger, approval state, and training admission
are unchanged.

The canonical helper's mode tie is hash-order-dependent on the formerly
non-dominant slices.  Alternate and fixed-axis rival programs therefore lexically
shadow `mode-list` with a deterministic highest-count/lowest-color tie rule, while
the canonical program remains untouched.  This is required for Racket/oracle
parity when the proposed variant deliberately selects those slices.

Adjacent seeds share the same seven lawful, distinct inputs and seed parity selects
the episode policy.  The retained pair uses three demonstrations and four queries.
Each query is identified from demonstrations alone against four declared programs:
`more_coherent`, `less_coherent`, `always_rows`, and `always_columns`.  The writer
uses public challenge bytes/IDs, keeps private settings and answers separate, sorts
by public ID, and rejects duplicate visible payloads before writing.

Evidence: `checks/parametric/tdd-green-final.log` (8/8 focused tests),
`checks/parametric/task-tests-final-wrapper.log` (17/17 staged task tests), and
`checks/parametric/axis-policy-v1/summary.json` (two paired episodes, 70 protected
Racket executions).  Identification is finite and only covers the four declared
rivals and the retained lawful domain; this remains a proposal, not a production
parameter contract.

