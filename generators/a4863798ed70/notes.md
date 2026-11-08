# Working notes: a4863798ed70

## Intended rule and input grammar

The selected authority keeps the gray track, hollow red frames, icon geometry,
and every position fixed.  Recover the 3–5 red-frame centers, sort them clockwise
around their shared centroid, and recolor each icon with the next clockwise
frame's original icon color.  Inputs use one of seven linked profiles coupling
grid size, frame count, frame size, and palette size; `scene_profile` is the only
advertised override because those dimensions are not independent.

The canonical authority remains Racket rule hash `0fa1a0b083d0`.  This review did
not edit Racket source, canonical examples, `RULE_HASH`, or the production
curriculum schedule.

## 2026-10-20 repair decisions

1. **Strict call validation.**  The previous `generate` path accepted booleans,
   floats, strings, and negative sample indices.  `_validate_call` now requires
   literal integer `seed` and `sample_index` values and a non-negative index.
   Evidence: `checks/before/checks/a4863798ed70_before_defect_lint.log` and
   `checks/after/checks/a4863798ed70_after_defect_lint.log`.
2. **Semantic declarations.**  The prior source copied all three genuine lesson
   competitors into `CANONICAL_SHORTCUTS`, although each mismatches all eight
   labeled canonical pairs.  They remain in `SEMANTIC_RIVALS` and
   `LESSON_COMPETITORS`; `CANONICAL_SHORTCUTS` is now empty.  This changes
   metadata only, not labels or generated grids.
3. **Preserve lawful generation bytes.**  `VERSION` remains `3.0.0` because the
   repair does not alter valid sampling and a version bump would perturb seeded
   generation.  Twenty-eight frozen valid cases (seven profiles × four
   difficulty settings) are byte-identical before and after the repair; see
   `checks/repair-regression/compare.json`.
4. **Tests.**  New source-bound tests live in
   `tests/test_repair_and_parametric.py`.  They cover strict scalars, semantic
   declaration truth, valid-output fingerprints, protected-Racket parity, and
   the proposed parametric episodes.  The focused suite passes 21/21.

## Lesson policy and measured limits

Production lessons use three demonstrations and one or more labeled queries.
The deterministic seven-slot linked-profile schedule is unchanged.  A
source-bound census materialized 100 lessons per band (300 total, 1,200 unique
inputs) and tested every held-out query rotation against the three declared
competitors.  It found 0 ambiguous production lessons and 0 ambiguous rotations,
with no materialization or scoring errors (`checks/lesson-census.summary.json`).
This finite result covers only declared rivals and sampled seeds; it is not a
proof of unique induction against every possible hypothesis.

The strict semantic smoke gate also passes 12/12 lessons and reports 0/48
ambiguous diagnostic rotations.  The full after battery is 12/12 green at final
generator SHA-256
`363750fa34cdfe60b32727f93d9c3ef69ce9e0a6df349175da7ad7258d239b86`.

## Proposed parametric extension (not production-approved)

`workspace/parametric/prototype.py` adds one episode-level parameter while
preserving the original object roles and input grammar:

- `cycle_direction=clockwise` is the canonical default and uses byte-identical
  canonical Racket text.
- `cycle_direction=counterclockwise` gives each frame the previous clockwise
  frame's color.

The direction is chosen once per episode.  Each retained episode has three
labeled demonstrations and one hidden-answer query; all three demonstrations
refute the other setting.  Both exact programs execute through the protected
Racket bridge.  Evidence for seeds 0 and 1 is under
`checks/parametric/cycle-direction-v1/`.  This prototype does not modify the
canonical generator API, authority, or approval state.

## Known limitation / open maintainer item

The required portable `task_tests` stage is blocked before pytest by the frozen
root fixture `test_generator_a4863798ed70.py`: it hard-codes a parent depth for
canonical data and imports the legacy `scripts.canonical_profile_gate` namespace.
Per the assignment, that fixture was not edited.  The maintainer must migrate it
to `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs` in a
future packet.  Diagnostic: `checks/task-tests/result.json`.
## Current reviewer considerations

Source SHA-256: `363750fa34cdfe60b32727f93d9c3ef69ce9e0a6df349175da7ad7258d239b86`.

# Decisions: a4863798ed70

## D1 — Repair the API boundary, not the sampler

**Prior choice:** `_validate_call` checked only difficulty and overrides.
Because Python treats booleans as integers and the sampler accepted several
other coercible values, 33 strict-scalar probes entered generation.

**New choice:** require `type(seed) is int`, `type(sample_index) is int`, and
`sample_index >= 0` before creating the generation context.  Literal integers,
including negative seeds, remain valid; only the sample index is constrained to
be non-negative because it indexes the curriculum schedule.

**Rejected alternatives:** coercing values with `int(...)` would silently merge
distinct calls and preserve the defect; validating only in `gen_ctx` would make
this task dependent on shared behavior and would not document its contract.

**Evidence and failure modes:** `checks/tdd/red.log` demonstrates the missing
boundary; `checks/tdd/green-attempt-3.log` and the final defect-lint log show the
repair.  The check is intentionally strict: `numpy.int64` and custom integer-like
objects are rejected unless the shared API later standardizes them.

## D2 — Distinguish canonical shortcuts from lesson competitors

**Prior choice:** `CANONICAL_SHORTCUTS = dict(SEMANTIC_RIVALS)`.

**New choice:** keep `reverse_clockwise_direction`, `reading_order_cycle`, and
`move_icon_shapes` in `SEMANTIC_RIVALS` and `LESSON_COMPETITORS`, but set
`CANONICAL_SHORTCUTS` to an empty typed mapping.  A canonical shortcut must fit
all labeled canonical pairs; these three mismatch all 8/8.

**Rejected alternative:** deleting the rivals entirely would make the semantic
gate pass by weakening the teaching contract.  They are useful, executable
competitors and remain required lesson checks.

**Evidence:** baseline semantic failure in
`checks/before/checks/a4863798ed70_before_semantic_gate.log`; focused declaration
test in `tests/test_repair_and_parametric.py`; final semantic pass in
`checks/after/checks/a4863798ed70_after_semantic_gate.log`.

## D3 — Preserve valid output bytes and keep version 3.0.0

The defects are validation and declaration errors, not a lawful-distribution or
label error.  Changing `VERSION` would perturb all seeded draws.  I therefore
kept version `3.0.0` and froze 28 valid generation hashes before editing: all
seven profiles crossed with `None`, easy, medium, and hard.  All 28 hashes match
after the repair (`checks/repair-regression/compare.json`).

A broader sampler rewrite was rejected because the baseline distribution,
profile-floor, diversity, override, grammar, authority, and self-check stages
were already green.  It would add unneeded label and curriculum risk.

## D4 — Keep the canonical Racket authority unchanged

The canonical program already matches all labeled examples and the production
mirror.  No evidence justified a rule change.  `RULE_HASH` remains
`0fa1a0b083d0`, the canonical clockwise program hash remains
`88247f36cb08b418744473a1e0d67c37c0264349d117abdb93f6f3e5ec1b994e`,
and the final authority-sync stage is green.

## D5 — Retain the seven linked profiles as one joint axis

Grid dimensions, frame count, frame size, and palette cardinality are coupled in
the source family.  Keeping `scene_profile` as the sole override avoids
advertising impossible cross-products.  The seven-slot deterministic schedule
also gives four exact canonical profiles in every band and already cleared the
profile-floor and diversity requirements.

Independent `grid_h`, `grid_w`, and `frame_count` axes were rejected because
most combinations would not correspond to an implemented, observable scene
manifold and could create accidental placement failures.

## D6 — Use three demonstrations and check every query rotation

The task declares `EXAMPLES_NEEDED=3`; the production lesson is three demos plus
query.  I preserved that policy and tested rather than increasing demo count.
The 300-lesson census materialized 100 lessons per band and held out all four
pairs in turn: 0/300 production ambiguities and 0/1,200 rotation ambiguities
against the three declared competitors.

This supports arbitrary one-query rotation for the measured sampler and rivals,
but finite sampling is not a uniqueness proof.  Undeclared hypotheses remain a
known limit.

## D7 — Select `cycle_direction` as the parametric extension

**Chosen parameter:** one episode-level enum with values `clockwise` and
`counterclockwise`; clockwise is byte-for-byte canonical.

**Why it fits:** it preserves the original object roles, framed-icon grammar,
color-transfer operation, and geometric ordering problem while changing one
semantically meaningful relation.  It can be hidden once per episode and is
easy to distinguish with ordinary source-family examples.

**Rejected alternatives:**

- rotating icon shapes instead of colors changes the operation and risks
  requiring shape extraction/reconstruction beyond the original family;
- cycling by two positions is ill-defined as a distinct rule for some small
  frame counts and can alias reverse direction;
- changing frame ordering to reading order removes the central geometric
  reasoning pattern rather than parameterizing it.

The prototype uses three demonstrations and one query.  For retained seeds 0
and 1, every demonstration distinguishes the selected direction from the other.
Exact Racket programs, public/private split, and protected-runtime identity are
in `checks/parametric/cycle-direction-v1/`.  It remains proposed and is not
wired into production generation.

## D8 — Do not edit the frozen root fixture

The required portable task-test stage fails preflight because the immutable
root test uses a fixed parent-depth canonical path and a legacy namespace.  The
assignment explicitly identifies it as a frozen fixture and assigns migration
to the maintainer.  I retained the failure in `checks/task-tests/result.json`,
kept new tests under `tests/`, and mark the overall return blocked on that
aggregate requirement rather than hiding or rewriting the inherited failure.

## D9 — Keep audit targets read-only

The two adversarial targets were inspected and tested without source edits.
`2a40849f3961` has no issue in the checked scope; `2ee5a50b2ab0` has a reproduced
teaching-distribution defect.  The latter should be repaired by its owner by
reserving marker color 8 or enforcing visibly changing horizontal and vertical
witnesses at lesson assembly.  See `AUDIT.md` and retained probes under
`checks/audit/`.
