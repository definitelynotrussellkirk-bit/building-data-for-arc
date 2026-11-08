# Working notes: 2a5919c40197

## Review repair (2026-10-05)

- Pinned canonical authority with `RULE_HASH = "bb6a3cb8ba31"`.
- Replaced the broad, internally conflicting override surface with one exact,
  observable axis: `scene_profile ∈ {canonical_anchor, width_extension}`.
- Alternated the two profiles by `sample_index`, so any four consecutive pairs
  contain two anchors and two width-extension witnesses. With three demos and
  one query, every query rotation leaves at least one of each in the demos.
- Declared and executable-tested the strongest canonical-fitting rival:
  “inspect only the first three cells of each row.” Wider examples always include
  a mixed row whose first three cells are equal and a later cell changes.
- Preserved broad variation on width-extension scenes (height `3..18`, width
  `4..18`, multiple row textures and difficulty-biased dimensions) without
  advertising probabilistic draws as exact public controls.
- Synchronized the selected base solution text to the exact canonical Racket
  program. This was a source-text repair only; canonical behavior did not change.

## Deliberate domain limits

`self_check` requires rectangular `3..18 × 3..18` inputs, at least three visible
input colors, and both a uniform and a non-uniform row. These constraints keep
training scenes informative but do not claim coverage of smaller, monochrome,
or single-output-color inputs on which the mathematical row rule is still
well-defined. The finite declared-rival census is evidence against named
shortcuts, not a proof of unique induction against every possible rival.

Imported associated notes retain original evidence/timestamps in
`evidence/associated_notes.jsonl`.

## Review extension (2026-10-22)

- Kept the canonical row-uniformity rule, public `scene_profile` axis, sampling
  distribution, and alternating lesson schedule unchanged.
- Tightened the public call contract in version `2.0.1`: `seed` and
  `sample_index` must now be literal nonnegative integers. This repairs the only
  failing baseline stage, which accepted 33 bool/float/string or negative-index
  calls. The retained regression is
  `tests/test_generator_2a5919c40197.py::test_seed_and_sample_index_are_strict_nonnegative_integers`.
- Added a separate proposed parametric prototype under `workspace/parametric/`.
  Its single hidden episode-level parameter is
  `line_axis ∈ {row, column}`, with canonical/default `row`. Controlled inputs
  contain exactly one uniform row and one uniform column so both settings are
  visibly distinct. Production generation and selected authority are untouched.
- Final evidence: 12/12 after-battery stages green; 15/15 portable task tests;
  300/300 production lessons and 1,200/1,200 query rotations refuted the declared
  first-three-cell rival; the parametric probe produced 48 matching Racket
  labels and 24/24 identifiable rotations across six episodes.
- The portable test snapshot initially exposed a dual-layout import collision in
  the prototype. The final loader accepts either dependency layout only when it
  is inside the same selected snapshot root, then compiles the exact selected
  generator bytes. The failed first task-test run is retained as evidence.

## Current reviewer considerations

Source SHA-256: `ab882fbcfe024233a84e2347b2463f99262a4efb7a2d5c6f16d7ca091994ab6f`.

# Decisions: 2a5919c40197

## D1 — Preserve the selected semantic rule

**Choice.** Keep the canonical full-row uniformity rule unchanged and pin it with
`RULE_HASH = "bb6a3cb8ba31"`.

**Original rationale.** The baseline documentation stated the same rule, but the
reason for its unpinned source arrangement was not recorded. Canonical execution
already solved all five labeled pairs.

**Alternatives considered.** Rewriting the canonical Racket program, retaining
multiple textually divergent authorities, or changing the task domain. A rule
rewrite would add semantic risk without fixing the generator defects.

**Probe.** Rule smoke and authority sync execute every canonical pair. Final
source parity is recorded in
`checks/final-after-rerun/checks/2a5919c40197_after_authority_sync.json`.

**Limit.** Text synchronization establishes one selected source group; it does
not itself approve the generator for training.

## D2 — Replace the old public controls instead of patching each one

**Choice.** Expose exactly one axis:
`scene_profile ∈ {canonical_anchor, width_extension}`. Unknown and retired axes
raise `ValueError`.

**Original rationale.** Unknown. The baseline exposed height, width, palette,
ratio, and texture controls, but their advertised ranges, degeneracy labels, and
difficulty-local behavior conflicted with generation and validation.

**Alternatives considered.** Keep all old axes and enumerate incompatibilities;
turn approximate random draws into exact controls; or make every internal row
texture public. Those designs create a large Cartesian contract without helping
the teaching objective.

**Probe.** The override checker exercised three cases across all three bands,
30 seeds each (270 draws), with zero findings or explicit rejections. The
unknown-key probe was rejected. Evidence:
`checks/final-after-rerun/checks/2a5919c40197_after_override_results.json`.

**Failure mode / limit.** Internal dimensions, palettes, and row textures remain
stochastic and therefore cannot be requested exactly through the public API.
That is deliberate rather than an undocumented control promise.

## D3 — Alternate exact anchors with direct shortcut witnesses

**Choice.** Even sample indices emit `canonical_anchor`; odd indices emit
`width_extension`. `EXAMPLES_NEEDED = 3`, so a four-pair lesson has three demos
and one query. Every query rotation retains at least one anchor and one witness.

**Original rationale.** The baseline had no source-bound guarantee that a lesson
contained canonical support or a counterexample to a plausible rival.

**Alternatives considered.** Independent random profile draws, a four-block
schedule with only one witness, or wider examples only. Random draws permit
all-anchor lessons; one witness can be held out as the query; wider-only lessons
lose exact canonical morphology.

**Probe.** The task test exhausts 12 cyclic starts in every difficulty band and
all four held-out positions. The large census checks 300 lessons and 1,200
rotations. Evidence: `checks/lesson-census.json`.

**Failure mode / limit.** The alternating schedule is predictable. That is
acceptable because profile parity does not determine row labels, but future
lesson assemblers must continue using consecutive sample indices or explicitly
recheck identifiability.

## D4 — Use a first-three-only rival as the primary semantic target

**Choice.** Declare “inspect only the first three cells of each row” in
`SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS`, linked to the
`late_change_after_three` witness.

**Rationale.** Every canonical row has width three, so this rival is behaviorally
identical on every public pair yet has a simple exact counterexample at width
four. It is stronger and more task-specific than generic guesses such as “paint
all rows black.”

**Alternatives considered.** First/last-cell equality, majority color, or
memorizing the finite canonical grids. The row-texture distribution supplies
some evidence against those, but the first-three rival is the most direct
canonical underdetermination and is executable under the shared semantic gate.

**Probe.** The exact input/output disagreement is retained in
`checks/shortcut-counterexample/counterexample.json`, with the authoritative
Racket execution in `checks/shortcut-counterexample/racket.json`.

**Failure mode / limit.** Passing one declared rival family does not rule out all
programs consistent with the demonstrations.

## D5 — Preserve exact canonical morphology without copying canonical grids

**Choice.** Use six index templates at exactly `3×3`, each with at least one
uniform and one mixed row and with three or four palette entries drawn from ARC
colors excluding `0` and `5`.

**Original rationale.** The baseline profile-floor evidence had only 2/60 exact
hits and no medium/hard support. Exact canonical support was therefore required.

**Alternatives considered.** Sample arbitrary random `3×3` grids; copy canonical
inputs; or allow output colors in the input. Arbitrary sampling gives weak
profile control, copying risks memorization, and input `0`/`5` can make the
transformation visually identity-like.

**Probe.** All five canonical inputs pass `self_check` and
`strict_canonical_like`; final profile floor has exact support in every band.

**Failure mode / limit.** The finite anchor-template family is intentionally
small. Generalization pressure comes from the alternating broad profile rather
than from anchor diversity alone.

## D6 — Make wider scenes broad but guarantee one decisive row

**Choice.** Draw heights `3..18`, widths `4..18`, and three to six non-output
colors. Insert one row whose first three cells are equal and a later cell changes;
fill remaining mixed rows with alternating, split, same-ends, one-minority, or
random patterns, plus one or more uniform rows.

**Original rationale.** Unknown. The baseline advertised `3..18`/`2..18` but
sampled only a narrow range, and some degenerate textures contradicted its own
validator.

**Alternatives considered.** Only width four; only the mandatory witness row;
or fully random rows. The selected design keeps the counterexample guaranteed
while varying size, color, row count, and other local heuristics.

**Probe.** The focused distribution test draws 120 examples per band, exactly 60
anchors and 60 witnesses, requires every witness to refute the rival, and
requires at least 115 unique grids per 120 draws.

**Failure mode / limit.** `self_check` intentionally excludes scenes with fewer
than three colors or only one output class. Such grids are mathematically lawful
but poor teaching examples and remain outside the documented generator domain.

## D7 — Treat validation as the lawful training grammar

**Choice.** Require rectangular ARC-color grids, dimensions `3..18`, at least
three colors, at least one uniform row, and at least one mixed row.

**Original rationale.** The baseline validator accepted low-signal minimal
impostors and conflicted with advertised degenerates.

**Alternatives considered.** Validate only shape/range, or accept all inputs on
which the Racket rule runs. Both permit lessons with all-identical outputs or
visually trivial transformations.

**Probe.** Canonical inputs pass; malformed, one-class, and collapsed examples
fail in task-local regressions; defect lint is green.

**Failure mode / limit.** This is a curriculum grammar, not the maximal domain of
the mathematical transformation.

## D8 — Synchronize selected Racket text, not behavior

**Choice.** Replace the selected base solution’s `raw_code` and `target_code`
with the exact canonical program text.

**Original rationale.** The divergent text was described by the checker as an
unsynchronized beautification; no design rationale was retained.

**Alternatives considered.** Leave the divergence advisory/failure in place or
rewrite the canonical source to match the base solution. The former blocks the
required gate; the latter changes the higher-authority source unnecessarily.

**Probe.** All three authorities now share exact SHA
`72e69fa2d29a33575fd623dc610554eb99b989013d47e570ee0b59aee253b339`
and normalized rule hash `bb6a3cb8ba31`; execution parity is 5/5 canonical
pairs.

**Failure mode / limit.** None identified beyond ordinary maintainer review of a
source-text delta.

## D9 — Add portable tests and retain real failures

**Choice.** Add nine tests using `reviewer_support.find_root`, `canonical_path`,
and `canonical_pairs`, and keep the red TDD run plus failed checker probes.

**Rationale.** The selected task-test stage snapshots into a portable layout;
fixed parent-depth imports would pass locally and fail in that runtime. Retaining
red evidence shows which behavior the implementation added rather than merely
recording post-hoc green tests.

**Alternatives considered.** Root-only pytest tests or ad hoc scripts. They are
not automatically discovered by the selected task stage and provide weaker
handoff guarantees.

**Probe.** `checks/tdd-red-v2.log` records eight expected baseline failures;
`checks/final-task-tests-rerun/result.json` records 9/9 passing in the staged
runtime.

## D10 — Reject coercible or negative generation indices

**Prior choice.** `generate` passed `seed` and `sample_index` directly into
`GenCtx`, while `schedule_profile` coerced `sample_index` with `int(...)`.
Consequently booleans, floats, numeric strings, and negative sample indices were
accepted even though they do not identify an exact replayable request.

**New choice.** Validate both values with one literal-nonnegative-integer helper
before constructing `GenCtx`, and use the same helper in `schedule_profile`.

**Reason and evidence.** The immutable before battery was 11/12 green; only
`defect_lint` failed, with 33 accepted invalid scalar probes. The focused test was
observed red before the edit and green afterward. The final battery is 12/12
green, with generator SHA
`ab882fbcfe024233a84e2347b2463f99262a4efb7a2d5c6f16d7ca091994ab6f`.

**Rejected alternative.** Coercing strings or integral floats was rejected
because it makes experiment identity dependent on implicit conversions and lets
`True` alias seed/index `1`.

**Limit.** This is an API/replay repair; it deliberately does not change any
lawful generated grid or label.

## D11 — Prototype one source-bound rule parameter outside production

**Parameter.** `line_axis`, allowed values `{row, column}`, default `row`.

**Semantics.** The canonical setting classifies complete rows. The alternative
classifies complete columns by the same uniform-versus-mixed predicate and emits
`5` for uniform lines and `0` otherwise. The exact canonical Racket bytes are the
row program; the column program changes one bounded row-access expression to the
corresponding column access.

**Episode policy.** Select the parameter once from seed parity for the complete
three-demonstration/one-query episode. Generate grids with exactly one uniform
line on each axis, so every labeled pair and every held-out rotation identifies
the selected setting. Public challenge projections hide the parameter, program,
and query answers.

**Alternatives considered.** Output-color changes were rejected as cosmetic;
thresholding the number of distinct values changes the predicate rather than the
structural axis; mixing row and column settings within one episode would make the
hidden rule incoherent.

**Evidence.** `checks/parametric/line-axis-v2/report.json` records six episodes,
both settings, 48 real Racket labels matching the Python assertion mirror, five
byte-exact canonical replays, one same-input differing-output witness, and 24/24
identifiable rotations.

**Status and limits.** Proposed prototype only. The controlled 4..7 grids and
two-value parameter domain are finite; the probe does not establish universal
identifiability or authorize production integration.

## D12 — Make the prototype portable without weakening source binding

**Failure observed.** The first portable task-test snapshot loaded
`puzzle_generators` from its repository mirror before the prototype asked the
strict helper for the equivalent execution-layout package. Three tests failed
with a cross-source-tree import error despite both trees belonging to the same
snapshot.

**Choice.** For this task-local prototype only, accept either package root when
it resolves inside the supplied snapshot root; reject any cached dependency
outside that root; compile the exact selected generator bytes directly.

**Evidence.** The initial snapshot result is retained under `checks/task-tests/`.
The fresh final snapshot under `checks/task-tests-v2/` passes 15/15 tests.

**Limit.** This is not a proposal to relax the shared selected-source loader.
The dual-layout accommodation is bounded to the prototype's self-check probe.
