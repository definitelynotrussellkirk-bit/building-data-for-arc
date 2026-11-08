# Working notes: c84e2a641055

## 2026-10-05 repair

Baseline `1.1.1` had no `RULE_HASH`, advertised dead or overlapping controls,
accepted singleton/line/solid-rectangle impostors, silently accepted unknown
keys, and had no semantic lesson contract. Its fixed four-shape monochrome
sampler did not expose the strongest canonical shortcut: dropping each color as
an independent object.

Selected repair:

- retained the canonical Racket authority unchanged;
- pinned `RULE_HASH = b08466eb063e`;
- replaced the old surface with six exact, observable, jointly constructible axes;
- enumerated fixed 4-connected polyominoes of 4..8 cells, excluding lines and
  solid rectangles;
- assigned two-color objects so the per-color shortcut necessarily disagrees;
- scheduled four profiles modulo 4, with 4 demonstrations per lesson;
- declared strict canonical support, witnesses, rivals, canonical shortcuts,
  and an executable lesson-identifiability hook;
- added portable regression tests and `workspace/review_probe.py`.

The first after-repair battery retained at `checks/after/` found one dead-band
warning because easy/medium/hard were byte-identical. A regression was added and
difficulty now selects guaranteed-distinct nuisance geometry while preserving
the same public axis values.

A final adversarial self-review then found a subtler proxy: the initial two-color
assignment made the floor-facing row one color and every upper row the other.
`checks/color_layers_red.log` preserves the failing regression. The final
assignment keeps one color absent from the floor (so per-color gravity remains
refutable), but puts both colors above the floor-facing row and randomizes the
remaining upper cells. This removes the pure vertical-layer cue without changing
the rule or public axes.

Final generator SHA-256:
`a373622249dcc16ae20d7db5770d19554ac62eef29ef49fc7c939b5791261207`.
## Current reviewer considerations

Source SHA-256: `a373622249dcc16ae20d7db5770d19554ac62eef29ef49fc7c939b5791261207`.

# Decisions — `c84e2a641055`

## D1 — Preserve the authority and repair the sampler

The selected Racket rule already implements the intended behavior: translate all
nonzero cells downward by one common offset until the lowest occupied row reaches
the final row. The before `rule_smoke`, `racket_lint`, and `authority_sync` stages
were green. I therefore changed no canonical/base data and no Racket code. The
repair is confined to the assigned generator, task-local tests/documentation,
and a task-local reviewer probe.

Rejected alternative: modify the rule or archival base copy to make the task
more general. That would hide the actual sampler/teaching defect and violate the
selected authority boundary.

## D2 — Replace the old surface with six observable axes

The baseline advertised controls that were ignored, overlapping, or incompatible
with the actual fixed-shape sampler. I retained only quantities that can be
observed exactly from a generated grid:

| Axis | Domain | Why retained |
|---|---|---|
| `grid_h` | 7..11 | exact canvas size; enough room for all shapes/travel |
| `grid_w` | 7..11 | exact canvas size; permits lateral placement diversity |
| `n_cells` | 4..8 | bridges canonical 4/5-cell cases to larger witnesses |
| `n_colors` | 1..2 | one color preserves canonical support; two refutes color-wise falling |
| `drop_distance` | 1..4 | exact transformation magnitude while avoiding identity |
| `bottom_profile` | flat/uneven | directly controls whether column-wise gravity can imitate the rule |

Every Cartesian product is constructible, so
`INCOMPATIBLE_OVERRIDE_COMBINATIONS` is empty. The generator checks requested
versus observed values before returning. Unknown keys and invalid difficulty
names raise immediately.

Rejected alternatives:

- Keep `texture`: it mixed semantic object count/shape conditions and could not
  be made independent without creating invalid domains.
- Keep a raw shape-name axis: a fixed catalogue would repeat the baseline's
  narrowness and make size/profile interactions brittle.
- Silently coerce impossible values: this would recreate override mismatches and
  make test results depend on hidden fallbacks.

## D3 — Enumerate fixed polyominoes instead of hand-picking shapes

The generator grows and normalizes all fixed 4-connected polyominoes of the
requested size, then filters by available dimensions and exact lower-boundary
profile. Lines and solid rectangles are excluded because they make the rigid
translation less structurally informative and were accepted too easily by the
baseline self-check.

This choice gives deterministic finite candidate pools, exact construction, and
far more geometry than the former four literals without needing a rejection
loop. Fixed rather than free polyominoes preserve reflections/rotations as real
nuisance variants.

Rejected alternative: random-walk growth with retries. It is simpler initially
but makes exact profile/size overrides probabilistic, creates timeout tails, and
complicates reproducibility.

## D4 — Use a deterministic four-profile teaching schedule

A complete lesson uses four demonstrations. Sample index modulo four schedules:

1. `mono_flat`: canonical-size 4-cell monochrome, flat bottom;
2. `mono_uneven`: canonical-size 5-cell monochrome, uneven bottom;
3. `multi_flat_large`: 6 cells, two colors, flat bottom;
4. `multi_uneven_large`: 7/8 cells, two colors, uneven bottom.

Any four consecutive indices contain all four profiles. This is stronger and
more inspectable than hoping independent random draws happen to contain the
necessary contrasts. It guarantees witnesses against identity, independent
column gravity, independent per-color gravity, and a canonical-size cap.

Rejected alternative: sample profiles independently. Even balanced marginals
permit complete lessons with no multicolor or no uneven example; witness
frequency is not the same as lesson identifiability.

## D5 — Separate public axes from difficulty

The first repair passed most gates but easy/medium/hard were byte-identical.
`checks/difficulty_red.log` records the failing regression. Difficulty now adds a
0/1/2 cyclic offset to one keyed shape draw. Every candidate pool has enough
members for this to guarantee three different nuisance geometries, while the
six public observable axis values remain identical across bands.

Rejected alternative: make difficulty change size, color count, or travel. That
would confound a public teaching profile with a nominal band and make lesson
coverage band-dependent.

## D6 — Design colors to refute per-color gravity without a row-label proxy

All five canonical examples are monochrome, so “drop each color independently”
fits them exactly. A two-color witness must place at least one color above the
object's lowest row and omit it from that lowest row; independent per-color
falling then moves it farther than rigid-object falling.

The first implementation made every bottom-row cell color A and every upper cell
color B. It refuted the rival but encoded a pure vertical layer rule. A final
manual adversarial review caught this despite green automated gates. The retained
red test is `checks/color_layers_red.log`.

The final assignment is:

- every floor-facing cell uses color A;
- at least one non-bottom cell also uses color A;
- at least one non-bottom cell uses color B;
- remaining non-bottom cells use a keyed random choice from both colors.

Thus B remains absent from the floor-facing row, preserving the rival witness,
while A and B both occur above it, breaking pure layer separation.

Rejected alternatives:

- Give both colors floor-facing cells: per-color gravity can then agree with the
  intended output.
- Use a fixed checkerboard: it introduces a different conspicuous color/geometry
  code and reduces nuisance diversity.
- Randomize all cells unconstrained: some draws fail to refute per-color gravity.

## D7 — Make the semantic contract executable

`rule_mirror` is a fresh-output Python mirror used for testing, never an authority
replacement. Four named competitors are executable:

- `identity`;
- `column_gravity`;
- `per_color_gravity`;
- `cap_five_cells`.

`CANONICAL_SHORTCUTS` contains the two that fit all canonical demonstrations:
`per_color_gravity` and `cap_five_cells`. Four witnesses map directly to rivals,
and `lesson_identifiable` requires exact labelled demonstrations to refute every
competitor. The four-profile schedule is what makes every full lesson pass,
including every single-query rotation of its five materialized pairs.

Limitation: these declarations define a finite hypothesis test. Passing them does
not prove uniqueness against arbitrary programs. Reports state that limitation
rather than calling the curriculum universally identifiable.

## D8 — Validation boundaries

`self_check` intentionally accepts only the generator's supported teaching
domain: rectangular integer ARC grids, 7–11 rows/columns, one 4-connected
nonzero object, 4–8 cells, 1–2 colors, at least two rows and columns, not a solid
rectangle, and 1–4 rows of travel. These conditions remove weak or malformed
training cases while remaining broader than the canonical examples.

Rejected alternative: let `self_check` accept every input on which the Racket
rule runs. The generator contract is a curriculum contract, not the full
mathematical domain of the authority.

## D9 — Evidence and reusable tooling

Tests were written to fail before each behavior change. Retained red evidence:

- `checks/task_tests_red.log`: baseline contract/semantic failures;
- `checks/difficulty_red.log`: byte-identical difficulty bands;
- `checks/probe_red.log`: absent reusable probe;
- `checks/color_layers_red.log`: pure vertical color layers.

`workspace/review_probe.py` discovers canonical pairs portably, verifies every
actual `CANONICAL_SHORTCUTS` declaration against them, finds exact generated
counterexamples, and checks all five query positions over requested consecutive
lesson starts. It deliberately labels its outputs as Python-mirror diagnostics;
final claims are confirmed with Racket-backed battery/census/apply commands.

The final large census uses 100 lessons per band and required query rotations.
It found no ambiguity against declared rivals in 300 lessons and 1,500 rotations,
but no count is presented as a theorem over undeclared hypotheses.
