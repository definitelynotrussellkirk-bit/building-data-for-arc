# Working notes: 9de65c6eed00

## Current rule and authority

The selected Racket authority (`RULE_HASH = 5c7d71fc1b03`) sorts nonzero objects
by descending size, takes the first two, normalizes each to its own bounding-box
top-left, removes normalized cells of the second from the first, and paints the
remainder in the first object's color. The canvas is the componentwise maximum
of their normalized bounding boxes. This review did **not** edit the authority.

The selected generator deliberately stays in the canonical two-object domain:
exactly two separated four-connected objects, distinct colors, unequal sizes,
background 0. A prior audit (`review-23201042e830bd3f:v0001`) showed that the
Racket authority uses the second-largest rather than the literal smallest object
when three objects are supplied. That input remains outside this generator's
validator and sampler; the discrepancy is recorded, not silently redefined.

## Reversed baseline decisions

The 2.0.0 baseline required the normalized smaller mask to be a strict subset of
the larger mask. That rejected canonical train example 0 and narrowed all sampled
lessons to one special case. Version 3.0.0 removes the subset requirement from
`self_check` and samples both subset and non-subset normalized overlaps.

The baseline advertised ten axes, including ignored helpful textures, ignored
size controls, and singleton controls. Version 3.0.0 exposes only four exact,
pixel-observable controls: `grid_h` 6..14, `grid_w` 9..18, `profile_id` 0..3,
and `palette_id` 0..5. Unknown, retired, out-of-range, boolean, string, and
floating-point values are rejected instead of being silently accepted.

## Curriculum and evidence

`EXAMPLES_NEEDED = 3`; one query follows three demonstrations. The shape profile
is `sample_index mod 4` and `LESSON_SCHEDULE_PERIOD = 4`:

- profile 0: canonical-style subset subtraction;
- profile 1: non-subset overlap and exact-mask-versus-bbox witness;
- profile 2: non-subset overlap where the smaller bbox is taller;
- profile 3: non-subset overlap where the smaller bbox is wider.

A shared D4 orientation, randomized separated placement, six ordered color-role
pairs, and variable dimensions prevent fixed position, orientation, and numeric
color-rank shortcuts. The declared competitors are `no_normalization`,
`bbox_subtraction`, `smaller_color`, `subset_only`, and `crop_to_large`.
`crop_to_large` fits all three canonical pairs, so profiles 2/3 explicitly teach
the max-canvas rule. The retained Racket-checked witness is
`counterexamples/crop_to_large.json`.

Final generator SHA-256:
`98e3565fc5906cde0d63a8e6361379d94162610db2287691285123df2c79703f`.
The final battery is 12/12 green. The 300-lesson production census materialized
1,200 labelled pairs with 1,191 unique inputs and found no ambiguity in 1,200
query rotations against the five declared competitors. Fixed-seed schedule
enumeration covered all 12 band/start lessons and 48 query rotations.

## Known limits and self-review

The sampler uses four curated shape-pair families rather than arbitrary connected
polyominoes. D4 orientation, placement, dimensions, and color roles vary, but a
learner could still memorize the finite families; broader shape synthesis is a
future extension, not claimed here. The declared-rival passes are finite evidence,
not proof against every possible hypothesis.

The two-object boundary intentionally masks the authority's behavior on three or
more objects. Expanding that domain would require a separate semantic decision
about whether the prose or executable authority should control. No current
training-approval claim is made by this review.
## Current reviewer considerations

Source SHA-256: `98e3565fc5906cde0d63a8e6361379d94162610db2287691285123df2c79703f`.

# Decisions for 9de65c6eed00

## D1 — Keep the executable authority unchanged

**Prior state.** The prose says “largest minus smallest,” while a retained audit
showed that the executable rule takes the first two size-ranked objects on a
three-object input. The selected sampler and every canonical input contain two
objects, where the two descriptions coincide.

**Decision.** Keep rule hash `5c7d71fc1b03` byte-identical and retain the exact
two-object domain. The prior audit remains open as a domain/authority question.

**Rejected alternative.** Editing the Racket rule to scan for the literal
smallest would change selected authority semantics beyond the canonical domain
without a maintainer decision.

## D2 — Remove the invented subset invariant

**Prior state.** The 2.0.0 validator required the smaller normalized mask to be a
strict subset of the larger. Canonical train example 0 violates that requirement,
so self-check rejected 1/3 canonical inputs.

**Decision.** A lawful selected input needs two separated distinct-color objects
with unequal sizes; exact normalized overlap is unrestricted. The difference is
nonempty because the larger object has more cells.

**Evidence.** `checks/before/` versus `checks/after/`; focused canonical tests in
`repo/generators/9de65c6eed00/tests/test_generator.py`.

## D3 — Use a four-profile cyclic teaching schedule

**Choice.** `sample_index mod 4` selects one subset profile, two non-subset exact-
mask profiles, and two profiles where the smaller bbox enlarges one output
dimension (profiles overlap in those categories). Each profile is jointly D4-
transformed and independently placed; color roles come from six ordered pairs.

**Rationale.** Three demonstrations from any four-pair window always include at
least two non-subset cases. Every query rotation therefore refutes `subset_only`,
while the expanded-canvas profiles refute `crop_to_large`, the one declared wrong
rule that fits all canonical pairs.

**Alternatives rejected.** Pure random shape synthesis had more nominal variety
but made it hard to guarantee every complete lesson contained each required
counterexample. A single fixed canonical template preserved the original
shortcut. The finite schedule is measurable and query-rotation safe.

**Evidence.** `checks/semantic-probe.json`, `checks/lesson-census.json`, and
`checks/schedule-census.json`.

## D4 — Make the control surface small and exact

**Prior state.** Ten axes included ignored `small_size`, `large_size`, helpful
textures with identical output, singleton palette/count axes, and unknown-key
acceptance. Difficulty-specific defaults also conflicted with the advertised
global dimension ranges.

**Decision.** Retain only `grid_h`, `grid_w`, `profile_id`, and `palette_id`.
Every legal value works in every difficulty band, is observable from pixels, and
is recorded in draw provenance. Retired or unknown controls fail explicitly.
Difficulty changes default frequency only, never legal override support.

**Evidence.** The shared override gate accepted 30,240/30,240 draws; the task tool
accepted 8,640/8,640 exhaustive joint cases.

## D5 — Preserve canonical-size support in every band

Profiles 0, 1, and 2 default to 6×9, 6×10, and 6×11 respectively. Profile 3
carries difficulty-dependent size expansion. This gives exact canonical profile
support in every 20-draw band without collapsing all dimensions to canonical
sizes. Final measurement: easy 15/20, medium 16/20, hard 16/20 exact hits.

## D6 — Declare only executable rivals

The generator declares five pure deterministic competitors and a witness for
each: no normalization, bbox subtraction, smaller output color, subset-only
handling, and cropping to the larger bbox. `CANONICAL_SHORTCUTS` contains only
`crop_to_large`, because it was verified to fit all three usable canonical pairs.
Task tests and probes iterate the live mappings rather than a copied name list.

## D7 — Retain honest limitations

The generated shapes come from four curated families. Joint orientation,
placement, dimensions, and palettes produce broad pixel diversity, but do not
prove generalization to arbitrary connected shapes or undeclared hypotheses.
The review therefore reports finite declared-rival evidence and does not claim
universal identifiability or training admission.

## 2026-10-25 native parametric review

A reviewer-authored native family now lives under `workspace/parametric/` with
`normalization_anchor ∈ {top_left, relative_corner}`.  `top_left` preserves the
selected canonical Racket program byte-for-byte.  In `relative_corner`, Step A
ranks the two objects and derives the smaller object's strict relative corner
from the two bounding-box centers; Step B aligns both normalized masks to that
corner before exact-mask subtraction.  The setting is episode-fixed and private.

The constructive sampler supports 2–6 prefix-stable demonstrations and 1–4
prefix-stable queries drawn from a privately shuffled four-query bank.  It keeps
inputs identical across settings, covers all four corners, and includes a dense
30×30 two-object boundary case.  A bounded audit covered 32 seeds, both settings,
all supported demonstration/query counts (1,280 episodes and public views), seven
fixed/partial/opposite-corner rivals, and 26 protected-Racket evaluations with no
findings.  Native qualification passed on seeds 0 and 17 with 3 demonstrations,
4 queries, and 40 protected-Racket labels.  A source-bound wrong-corner witness
received reviewer replay and independent recheck.  This is reviewer-ready only;
owner integration, fresh acceptance, canonical approval of the alternative, and
training admission remain pending.
