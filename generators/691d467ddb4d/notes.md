# Generator notes: 691d467ddb4d

## Intended rule and authority

Find every 4-connected yellow (`4`) object, select the uniquely leftmost one by
its minimum column, and recolor that entire object green (`3`). The canonical
Racket authority was not changed. `RULE_HASH` remains `cbcf1f4c6292`.

## Current sampler (version 2.0.0)

The generator places connected shapes in separated 2×2 lattice blocks. This is
constructive rather than rejection-based: the requested target plus exactly
`n_right` right-side distractors is always realized for every documented legal
combination, including `grid_h=8`, `grid_w=10`, `n_right=3` in every difficulty
band. Objects cannot merge because neighboring block origins have a one-cell
separator.

Only three override axes are declared because they are directly observable in
the returned pixels:

- `grid_h`: 8..14
- `grid_w`: 10..18
- `n_right`: 1..3

Unknown keys and non-integer values fail closed. Difficulty changes the weight
of `n_right` but not its legal support. Heights and widths retain strong support
for canonical-size profiles while still drawing from their complete domains.

## Reversed decisions

The prior sampler anchored every selected object in minimum column 0 or 1. A
retained 600-draw census found 319 targets at column 0 and 281 at column 1, so
“recolor an object only when it touches the first two columns” matched every
generated label while failing the canonical test query at column 2. The current
three-profile schedule replaces that edge-only policy:

1. `interior_near`: target starts at column 2 and below a distractor.
2. `interior_far`: target uses the farthest feasible interior target column and
   remains below a distractor.
3. `edge`: target begins at column 0 or 1 to preserve relevant edge cases.

Thus any consecutive three examples contain two interior counterexamples. The
previous palette and “texture” metadata were also removed: they were not honest,
independently observable axes and some advertised values collapsed to the same
pixels.

## Teaching contract

`EXAMPLES_NEEDED=2` and the period-3 schedule are paired with executable rivals:

- `border_touch_first_two_columns`
- `topmost_object`

Interior profiles are witnesses for both: the target is away from the first two
columns and below at least one distractor. `lesson_identifiable` validates all
labels and rejects a lesson when either declared rival fits every demonstration.
The contract supports any query rotation of a three-pair lesson, not only the
production order.

## Reproducers and verification

- Current dual-rival witness:
  `counterexamples/shortcut_witnesses_v2.json`.
- Independent oracle and distribution tool:
  `workspace/reference_probe.py`.
- Focused regressions:
  `tests/test_generator.py` (48 tests).
- Final generator SHA-256:
  `3910cea3855ddf3e0e0093600917a603e1d92f86b48d5f0c91775fc6b7c97433`.
- Full after battery: 12/12 green with required query rotations.
- Large lesson census: 300 production lessons and all 900 held-out query
  rotations, zero declared-rival ambiguities or scoring errors.
- Independent 600-draw census: 134/200 interior targets in each difficulty band;
  179, 198, and 199 unique inputs in easy, medium, and hard respectively.

## Known limits

The executable lesson check proves separation only from the declared rivals,
not from every conceivable program. The sampler deliberately uses compact
connected shapes that fit 2×2 blocks and one-third edge profiles; it does not
span every lawful object geometry or every possible target coordinate. The
fixed-seed period enumeration covers all three declared schedule starts in every
band, while the larger census is randomized rather than exhaustive over seeds.
## Current reviewer considerations

Source SHA-256: `3910cea3855ddf3e0e0093600917a603e1d92f86b48d5f0c91775fc6b7c97433`.

# Decisions for 691d467ddb4d

## D1 — Replace rejection placement with a constructive lattice

**Choice.** Use separated 2×2 placement blocks and compute feasible target
columns before choosing exact origins.

**Why.** The old sampler coupled “leftmost” to the canvas border and could not
reliably honor all advertised controls. Constructive placement makes exact
object count and separation structural, including the minimum `8×10` canvas
with three distractors.

**Rejected alternatives.** Increasing rejection retries would retain hidden
failure probabilities and make exact override support seed-dependent. Generating
arbitrary shapes first and packing them afterward would add complexity without
helping the reviewed defect.

**Probe.** `test_component_count_is_exact_and_objects_do_not_merge` plus the
11,970-draw override report.

## D2 — Declare only three observable axes

**Choice.** Keep `grid_h`, `grid_w`, and `n_right`; remove palette and texture
controls.

**Why.** These three values are unambiguously recoverable from pixels. The prior
palette/texture metadata was either fixed by the rule or degenerate, so it
created apparent diversity without independent observable support.

**Rejected alternative.** Retaining dead keys for backward compatibility would
continue to mislead authoring and the override checker. There is no documented
consumer requiring them.

**Failure mode.** A future axis should not be added unless all legal values are
constructive in every declared band and `observe_overrides` can recover it.

## D3 — Weight canonical sizes without narrowing legal support

**Choice.** Draw every legal height and width through `GenCtx`, with additional
weight on `(8,10)`, `(9,11)`, and `(10,12)` profiles. Weight `n_right` toward 1,
2, or 3 for easy, medium, or hard while preserving all three values everywhere.

**Why.** Canonical-scale scenes remain common enough for the profile floor, but
exact overrides and the default sampler still cover the full documented domain.

**Rejected alternative.** Band-specific hard exclusions would make difficulty
part of the validity contract and multiply incompatible override cases.

## D4 — Use a period-3 position schedule

**Choice.** Emit two interior profiles followed by one edge profile. Interior
targets are below a forced distractor.

**Why.** Every two-demo subset of a three-pair window contains a counterexample
to both reviewed shortcuts, regardless of which pair becomes the query. Keeping
an edge profile prevents the repair from replacing “always edge” with “never
edge” and retains canonical relevance.

**Rejected alternatives.** Fully random target position has a nonzero chance of
producing an ambiguous two-demo lesson. Always-interior placement would create a
new inverse support restriction. Raising the minimum to three demonstrations is
unnecessary once two demonstrations are deterministically informative.

**Evidence.** The 300-lesson/900-rotation census and 27-rotation complete
fixed-seed schedule enumeration.

## D5 — Name executable rivals instead of relying on prose

**Choice.** Declare `border_touch_first_two_columns` and `topmost_object`, with
witness predicates and a source-level `lesson_identifiable` hook.

**Why.** Both are simple, plausible rules induced by the old layout. Executable
rivals turn “teachable” into a replayable property and make query-order failures
visible.

**Rejected alternative.** A generic “looks diverse” heuristic would not compare
predictions and could pass while the wrong rule still fits every demo.

**Limit.** Passing two named rivals does not establish unique induction among
all programs. New observed shortcuts should be added as named competitors and
minimal witnesses rather than treated as covered by the current result.

## D6 — Keep Racket authority unchanged

**Choice.** Do not edit the canonical ledger or Racket rule; pin
`RULE_HASH="cbcf1f4c6292"`.

**Why.** Canonical outputs and an independent Python oracle agree. The defect was
input support and contract metadata, not rule semantics or labels.

## D7 — Build a portable independent review tool

**Choice.** Add `workspace/reference_probe.py`, with its own component finder,
intended output, shortcut outputs, observable statistics, and census CLI. Locate
canonical data via `reviewer_support.find_root`/`canonical_path` rather than
working-directory or fixed-parent assumptions.

**Why.** This lets future agents distinguish sampler defects from generator-
internal mirror coupling and rerun the same probe in isolated task-test runtimes
or fresh packet extractions.
