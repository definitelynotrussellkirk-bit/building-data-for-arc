# Working notes: 9349fabc466a

## Baseline finding

The selected 2.1.1 baseline sampled only exactly two same-color markers per
color. That distribution fit the three canonical examples but left their main
ambiguities untouched: “exactly two only,” “use the first pair only,” reverse
color priority at crossings, and bounding-box connection. It also omitted the
required `RULE_HASH`, declared several singleton/unprobeable axes, silently
ignored helpful texture overrides, and had no executable semantic contract.

The before battery, bound to generator SHA-256
`44a51b21c5a88ee7380d8e604fa56b972866b710231fc83a197418670620abb8`,
finished with 7 green, 2 advisory, and 3 failed stages. See
`checks/before/checks/9349fabc466a_before_battery_summary.json`.

## Selected repair

Version 3.0.0 pins canonical rule hash `bde71b91a345` and replaces the old
exactly-two sampler with a deterministic two-profile curriculum:

- every even accepted index is a comprehensive teaching case;
- every odd index draws one of pair, collinear-triplet, rectangle, crossing, or
  unaligned-distractor layouts;
- dihedral transforms and offsets vary placement without changing semantics;
- half the stream uses 7×9 or 8×8 canonical-scale grids in every difficulty;
- exact controls are limited to observable `grid_shape`, `n_colors`, and
  `palette_kind` axes, and unknown or invalid overrides are rejected.

The teaching case refutes all four declared rivals in one grid. Placing one at
every even index means any four consecutive accepted pairs retain at least one
teaching case after any single pair is held out as query. The generator exposes
an independent Python oracle, four executable rivals, four witness predicates,
an override observer, strict-profile validation, schedule profiles, and a
lesson-level identifiability hook.

## Regression tests and evidence

Task-local tests were written before the repair and initially failed on missing
oracle/semantic/override/profile behavior. The final suite has 17 passing tests
covering all canonical pairs, invalid and exact overrides, canonical-profile
support, all four rivals/witnesses, deterministic color realization, and every
query rotation for twelve consecutive four-pair lesson starts.

Final generator SHA-256:
`933d3b581683cd51c37ad25c5721174e7f38a2d62a62ecb55e61f5f131d680d6`.
The completed after battery is 12/12 green. The semantic gate measured 350/600
strict-like draws, 4/4 witnesses firing, 4/4 canonical-ambiguous rival claims
verified, 12/12 smoke lessons identifiable, and 0/48 ambiguous smoke rotations.
The 100-lessons-per-band census materialized 300 lessons / 1,200 pairs and found
0/1,200 ambiguous query rotations against the four declared rivals, with 736
unique inputs. Evidence is under `checks/after/`, `checks/task-tests/`, and
`checks/lesson-census.json`.

## Limitations

The finite checks establish separation only from the four declared rivals, not
from every conceivable hypothesis. The sampler uses five discrete grid shapes
and three contiguous three-color palette families rather than arbitrary legal
dimensions or color subsets. It intentionally does not generate the canonical
5×7 profile, although the oracle and tests accept that canonical example. The
canonical Racket program and canonical data were not changed.
## Current reviewer considerations

Source SHA-256: `933d3b581683cd51c37ad25c5721174e7f38a2d62a62ecb55e61f5f131d680d6`.

# Decisions for 9349fabc466a

## D1 — Keep the canonical Racket rule unchanged

**Original rationale.** The baseline notes did not explain why the rule had been
chosen. Direct inspection of the canonical examples and rule showed a coherent,
more general operation than the baseline sampler exercised: every same-color
row/column span is filled, multiple markers can induce multiple spans, existing
markers remain, and the numerically smallest eligible color wins an overlap.

**Alternatives considered.** Narrow the rule to exactly two markers per color;
change overlap priority to encounter order; or modify canonical examples to fit
the old summary. Those alternatives would encode baseline sampling accidents
rather than the existing authority.

**Probe and result.** An independent Python oracle matched all three canonical
pairs, and the final `rule_smoke`, `racket_lint`, and `authority_sync` stages are
green. The canonical file and Racket source were not edited.

**Failure mode / limitation.** The Python oracle is still a second
implementation and could share a mistaken interpretation; source-bound Racket
smoke tests and unchanged authority reduce but do not mathematically eliminate
that risk.

## D2 — Replace the exactly-two distribution with semantic templates

**Original rationale.** The 2.1.1 generator always emitted exactly two markers
per color, even though the canonical rule accepts more. This made
`exactly_two_only` and `first_pair_only` indistinguishable from the intended
rule on every generated input.

**Selected choice.** Use six small 7×7 local templates—pair, collinear triplet,
rectangle, crossing, unaligned distractor, and comprehensive teaching—then
apply a dihedral transform and embed them at a variable offset. Each color has
2–4 markers and every emitted grid has a visible rule effect.

**Alternatives considered.** Fully random marker placement with rejection;
mutating the old two-marker sampler; or generating only comprehensive cases.
Fully random placement made witness coverage and lesson ordering difficult to
reason about. A small mutation retained too much of the old shortcut. Teaching
cases only would reduce morphological variety and make the curriculum overly
regular.

**Probe and result.** The semantic gate saw all four witnesses in every band,
and the 300-lesson census found no declared-rival ambiguity. Diversity measured
82% unique inputs and outputs over 300 sampled pairs.

**Failure mode / limitation.** Template-based generation is intentionally not an
exhaustive sampler of all lawful point arrangements. A learner may discover a
new template or parity shortcut not represented by the four declared rivals.

## D3 — Alternate comprehensive teaching and varied cases

**Original rationale.** Unknown; the old generator had no explicit lesson
schedule. Witness frequency alone is insufficient because three individually
valid demonstrations can jointly omit the one counterexample needed to reject a
shortcut.

**Selected choice.** Every even accepted sample index is comprehensive; every
odd index is varied. Production lessons use four consecutive pairs (three demos
and one query). Any four-pair window contains two teaching cases, so holding out
one pair leaves at least one comprehensive demonstration.

**Alternatives considered.** Randomly choose teaching cases at a target
frequency; put exactly one teaching case at index 0 of each nominal block; or
resample whole lessons after ambiguity is detected. Random frequency has no
per-lesson guarantee. One-per-block fails under shifted starts or if that pair is
the query. Whole-lesson rejection is more expensive and obscures the simple
schedule invariant.

**Probe and result.** Task-local tests exhaust all four query positions for 12
cyclic starts. The semantic smoke test found 0/48 ambiguous rotations, and the
100-lessons-per-band census found 0/1,200.

**Failure mode / limitation.** The guarantee assumes consecutive accepted
indices and one query among four materialized pairs. A downstream assembler that
skips indices, uses a different demonstration count, or combines unrelated
streams must re-run identifiability checks.

## D4 — Declare four executable canonical-ambiguous rivals

**Original rationale.** No prior semantic contract existed. The rivals were
chosen from concrete ambiguities left by the canonical pairs and baseline:
`exactly_two_only`, `first_pair_only`, `highest_color_wins`, and
`bounding_box_connect`.

**Alternatives considered.** A prose-only list, a generic mutation fuzzer, or a
much larger hand-written rival library. Prose cannot be gated; mutation fuzzing
does not necessarily encode plausible induction rules; a large speculative
library would be costly and brittle.

**Probe and result.** Each rival was verified to match every usable canonical
pair and to differ from the pinned reference on generated witnesses. The
semantic gate checked 60 claims per rival and the task tests independently
assert both halves.

**Failure mode / limitation.** Passing against these four rivals is finite
separation, not proof of unique induction. Undeclared rules may still fit all
training pairs.

## D5 — Use five discrete shapes with recurring canonical-scale profiles

**Original rationale.** The baseline advertised roughly 5–12 dimensions but had
no source-linked profile guarantee. The canonical examples include 5×7, 7×9,
and 8×8 grids with two nonzero colors.

**Selected choice.** Expose exact shapes 7×9, 8×8, 10×12, 14×14, and 18×18.
Every even index alternates between 7×9 and 8×8 regardless of difficulty; odd
indices draw from a band-scaled subset. This provides canonical-scale support
while allowing substantially larger hard cases.

**Alternatives considered.** Arbitrary height/width axes; reproduce all canonical
shapes including 5×7; or use only canonical shapes. Independent dimensions
create a larger override matrix and many equivalent controls. The 7×7 local
teaching template does not fit 5×7 without a second geometry. Canonical-only
sizes would underexercise scale.

**Probe and result.** Profile floor passed in all bands with 34/60 exact-profile
draws. The independent oracle and canonical tests still accept the 5×7 example.

**Failure mode / limitation.** The production sampler does not emit 5×7 or
arbitrary rectangles, so profile support is partial rather than a reconstruction
of the entire canonical dimension distribution.

## D6 — Restrict exact controls to observable axes

**Original rationale.** The old `AXES` declared controls such as textures that
were ignored or singletons, causing override failures and misleading callers.

**Selected choice.** Keep only `grid_shape`, `n_colors`, and `palette_kind`.
Validate types and domains before generation, reject unknown controls, and expose
`observe_overrides` so the matrix can verify exact realization.

**Alternatives considered.** Retain old axis names as aliases; silently clamp
invalid values; or expose dihedral/layout/offset as public axes. Aliases would
preserve dead semantics, clamping would hide caller mistakes, and low-level
layout controls would greatly enlarge joint-domain testing without a current
training need.

**Probe and result.** All 3,780 override-matrix draws were accepted with zero
findings. Task tests cover exact overrides in all bands and reject unknown,
out-of-range, and boolean integer inputs.

**Failure mode / limitation.** The public axis surface is deliberately smaller;
experiments needing exact layout or orientation must add a tested control rather
than relying on internal RNG labels.

## D7 — Use contiguous low/mid/high palettes

**Original rationale.** Unknown. The canonical rule is color-relative except
for numeric overlap priority, so the distribution must exercise different
numeric ranges while preserving an unambiguous smallest color.

**Selected choice.** Palette families are `(1,2,3)`, `(4,5,6)`, and `(7,8,9)`;
`n_colors=2` takes the first two and `n_colors=3` uses all three.

**Alternatives considered.** Uniformly sample arbitrary color subsets or include
color 0 as a marker. Arbitrary subsets provide more color diversity but make
exact palette override observation less direct. Color 0 is the fixed background
and cannot be a marker.

**Probe and result.** Diversity observed all ten ARC cell values including
background across the sample, while exact palette overrides were fully
observable. Crossing templates exercise priority in every numeric family.

**Failure mode / limitation.** Contiguous families do not cover every gap or
permutation of marker colors; an unintended learner could exploit that regularity.
The geometry and rule do not depend on contiguity, so a future expansion should
add arbitrary sorted subsets with a robust observer.

## D8 — Add task-local TDD regressions and preserve finite-scope claims

**Original rationale.** The selected task had no task-local regression suite.
Battery passes alone did not test all cyclic starts or verify that each declared
shortcut really fits the canonical pairs.

**Selected choice.** Add 17 portable tests using
`reviewer_support.find_root(__file__)` and `canonical_pairs`. Tests cover the
canonical oracle, controls, profile/witness coverage, rival validity, 12 lesson
starts × 4 query rotations, and deterministic color realization.

**Alternatives considered.** Modify frozen root fixtures or rely solely on the
shared battery. Frozen fixtures are not patchable, and the small semantic smoke
sample does not exhaust this schedule's cheap cyclic starts.

**Probe and result.** The tests failed before implementation for the intended
missing behavior and now pass 17/17 in both the working packet and the fresh
patch replay.

**Failure mode / limitation.** The tests are source-specific and sample finite
seed ranges. They should complement, not replace, the larger source-bound
battery and census.

## Final self-review for new shortcuts/restrictions

The alternating schedule itself creates an even/odd regularity and the palette
families are contiguous; neither affects label correctness, but both are
potential metadata-free distribution shortcuts if sample order is exposed. A
small witness against schedule dependence is that odd cases span five layouts
and all eight dihedral transforms, while query-rotation checks hold for every
start residue tested; nevertheless, exports should shuffle completed lessons
rather than expose raw sample indices.

## D9 — Native completion-derived frame family (review-b596ea5e28e57060)

**Defect addressed.** The approved ordinary generator had no native parametric
adapter, promotion contract, source inventory, qualification, or sequential
causal witness for this round.

**Selected design.** Keep the exact canonical span-completion program as
`postprocess=canonical`. The alternative `completion_frame` first runs that
program, identifies the color with the largest set of cells newly created by
completion (numeric-color tie break), and paints color 9 on the one-cell outer
frame of that new-cell bounding box. Every scene includes a larger diagonal
input-marker bounding-box decoy that creates no span, so Stage B cannot be
implemented by framing the largest original object.

**Evidence.** The task-local bounded audit swept 32 seeds, both settings, all
2–6 demonstration counts, all 1–4 query counts, 8,320 labeled pairs, 320 causal
separations, and 40 protected-Racket labels plus 20 protected counterfactuals
with no findings. Native qualification passed four jobs. The retained protected
witness replays the qualified alternative against `wrong_intermediate.rkt` on a
30×30 case. Target tests pass 25/25; public projection checks pass 16 single-query
views and 24 private-field invariance mutations.

**Limits / next action.** This is finite reviewer evidence, not universal rule
uniqueness. Owner integration must preserve the exact source binding, rerun
native qualification and causal replay, then perform fresh acceptance. No
training admission is claimed.
