# Working notes: 67ec1565020d

## Current authority and intended rule

Canonical Racket authority is unchanged and pinned as `RULE_HASH = "b45100a04df9"`.
For each monochrome 4-connected nonzero component, compare its tight bounding-box
width and height. Recolor the component's occupied cells with 2 when wide, 3 when
tall, and 4 when square. Background and holes inside the bounding box remain 0.

## Repair in review-d0dac661bdcda24c

Selected baseline: generator v1.1.1, SHA-256
`9352d6f059db06fd37c727cfe59a391d255b227cea45fe98ffc58a5f9e33e90b`.
Prior return `review-da130648b0bc2752:v0001` was used as the lead for finding
A67-1: every canonical and sampled object was a solid rectangle, so the plausible
rival "classify by aspect, then fill the whole bounding box" was observationally
indistinguishable.

The generator is now v2.0.0, SHA-256
`2efca0bd793421b579ca67617984517d0a2ced51db10673a8d6cc84b822d8dc3`.
Default draws contain at least one irregular connected component and reuse one
input color across different aspect classes. Those witnesses refute both retained
canonical-fitting rivals:

- `fill_bounding_boxes`: paints every bbox cell after the correct classification;
- `group_by_color`: merges disconnected components that share an input color.

The sampler randomizes connected shape masks, colors, aspect order, and placement.
It has a constructive slot fallback for crowded exact-control combinations.

## Public controls

The only advertised axes are exact integer controls:

- `grid_h`: 8..14;
- `grid_w`: 9..14;
- `n_blobs`: 3..6;
- `n_distinct_colors`: 1..6, not greater than `n_blobs`.

Unknown, retired, non-integer, Boolean, and out-of-range controls reject. The
`n_blobs`/`n_distinct_colors` incompatibility is reported with both axis names.
Default core draws favor 10x10, four objects on easy/medium, six on hard, and
three foreground colors when feasible. This keeps an exact canonical
size/palette profile in every band while ordinarily supplying the repeated-color
witness.

## Validation and evidence

`self_check` accepts the canonical inputs and the documented task domain: an
8..14 by 9..14 rectangular integer-color grid with 3..6 nonzero monochrome
components and at least one wide, tall, and square bounding box. It intentionally
does not require irregularity or repeated colors, because the canonical examples
are solid and exact overrides may lawfully request one color per component.

Final source-bound battery: 12/12 stages green under `checks/after-final/`.
Portable task tests: 67/67 passed under `checks/task-tests-final/`. The tests cover
canonical parity, exact joint controls, invalid controls and grids, constructive
fallback, both rivals, determinism, and canonical profile support.

A source-bound lesson census materialized 100 lessons per band, each with three
ordered demonstrations and one query, then held out every pair once. Production:
300/300 lessons, 0 ambiguities. Rotations: 1,200/1,200, 0 ambiguities. It checked
1,200 unique inputs with no materialization, hook, or scoring errors. This is
finite evidence against the two declared rivals, not a proof against every
possible induction rule.

## Known limits and open questions

- The grammar is restricted to 3..6 separated monochrome components on 8..14 by
  9..14 canvases; it does not cover touching components or arbitrary object count.
- The mandatory irregular witness is assigned to a square-bbox component before
  plan shuffling. Other classes may also be irregular, but this creates a benign
  distribution correlation worth revisiting if broader morphology is desired.
- Canonical examples alone still permit both declared shortcuts; generated
  lessons, rather than a rule change, provide the disambiguating evidence.
- Catalog approval and training admission remain unchanged and unverified.
## Current reviewer considerations

Source SHA-256: `2efca0bd793421b579ca67617984517d0a2ced51db10673a8d6cc84b822d8dc3`.

# Decisions: 67ec1565020d

## D1 — Keep the selected Racket authority unchanged

**Choice.** Preserve the canonical rule and canonical examples; pin
`RULE_HASH = "b45100a04df9"` in the generator.

**Rationale.** Canonical comparison and rule-smoke evidence show the labels are
internally consistent: classify each monochrome 4-component by tight bbox aspect
and recolor only its occupied cells. The defect was generator support, metadata,
and validation, not reference execution.

**Alternatives considered.** Rewrite the rule to fill bounding boxes; restrict the
written task to solid rectangles; change output colors.

**Probe and failure mode.** The retained irregular witness has official output 0
at `(6,2)` while bbox filling predicts 4. Changing the rule would legitimize the
shortcut instead of teaching the original mask-preserving behavior. Final rule
smoke, Racket lint, and authority sync pass with no authority edit.

## D2 — Treat the prior audit as a lead, then reproduce it on final-source tooling

**Choice.** Use `review-da130648b0bc2752:v0001` to identify A67-1, but bind the
repair and final claims to the selected baseline and final source hashes.

**Original rationale.** Unknown; the v1.1.1 sampler appears to have chosen three
very simple solid primitives for reliability.

**Alternatives considered.** Ignore retained audit evidence; accept the solid-only
domain as intentional; reread every historical return.

**Probe and failure mode.** The selected baseline SHA matches the prior audited
SHA. The fresh task tests verify that both retained rivals fit all four usable
canonical pairs, and the final generated witness is independently Racket-labelled.
Treating the old return as current measurements would be a provenance error, so
its counts are not reused as final counts.

## D3 — Generate connected masks, not a larger fixed pattern library

**Choice.** Construct each requested aspect from a bbox-spanning connected seed,
then randomly grow it; force one non-solid square-bbox component on ordinary and
exact-control draws.

**Rationale.** A generative mask grammar gives much broader morphology than a
list of rectangles while preserving connectivity and exact bbox dimensions. The
forced missing cell directly separates occupied-mask preservation from bbox fill.

**Alternatives considered.** Add one fixed L-shape; use only polyomino templates;
allow disconnected shapes; make every object irregular.

**Probes.** `test_default_inputs_refute_both_canonical_shortcuts` samples 64
unique deterministic inputs per band and requires a nonrectangle on every draw.
The Racket witness at seed 91000/sample 2 records the exact official/rival split.

**Failure modes and limits.** Disconnected masks would change object semantics;
forcing every shape irregular would move too far from canonical support. The
mandatory witness is square-class before plan shuffling, creating a documented
morphology/aspect correlation.

## D4 — Reuse a color across wide and tall components by default

**Choice.** When fewer colors than objects are requested, assign the first palette
color to both a wide and a tall component before shuffling the object plan.

**Rationale.** Canonical pairs permit a plausible global input-color-to-output-
color mapping because colors do not need to span aspect classes. One repeated
color with conflicting intended outputs refutes that rival locally.

**Alternatives considered.** Always use distinct colors; repeat colors without
controlling aspect; use one color for every object.

**Probes.** The focused 64-draw-per-band test requires
`color_spans_aspects(grid)` and direct disagreement with `group_by_color` on every
default draw. The 300-lesson census tests the executable rival in production and
all four query rotations.

**Failure modes and limits.** Exact `n_distinct_colors == n_blobs` lawfully removes
this witness, so it is a default curriculum guarantee rather than a universal
validator invariant. One-color scenes remain lawful and still teach componentwise
processing through the aspect outputs.

## D5 — Expose only four exact, observable controls

**Choice.** Advertise `grid_h`, `grid_w`, `n_blobs`, and
`n_distinct_colors`; reject unknown and retired controls. Report
`n_distinct_colors > n_blobs` as an incompatibility involving both axes.

**Original rationale reversed.** The baseline exposed texture/palette/density-
style declarations whose behavior was dead, overlapping, or not source-bound.
The exact original intent for those declarations is unknown.

**Alternatives considered.** Repair every legacy aesthetic axis; keep negative
textures in the ordinary domain; remove overrides entirely.

**Probes.** Joint exact-control tests cover object/color combinations in every
band, single palette overrides 1..6, invalid types/ranges, retired names, and the
axis-pair diagnostic. Final override and lint stages pass.

**Failure modes and limits.** Exact object/color combinations can crowd small
canvases. The constructive fallback in D6 prevents silent underproduction.

## D6 — Combine randomized rejection placement with a constructive fallback

**Choice.** Try free random 8-separated placement first; after bounded retries,
partition the canvas into 2x2, 2x3, or 3x2 slots and place one object per slot.

**Rationale.** Random placement avoids an overly regular default layout, while a
constructive path guarantees every advertised exact combination can be produced
without unbounded retries.

**Alternatives considered.** Pure rejection sampling; constructive slots on every
draw; silently reduce object count when crowded.

**Probe and failure mode.** A regression monkeypatches `_place_shape` to fail and
checks 3..6 objects, exact counts, validator acceptance, and both semantic
witnesses. Silently reducing counts would violate the override contract; an
unbounded retry loop could hang the battery.

## D7 — Bias the core profile to 10x10 and four easy/medium objects

**Choice.** Favor 10x10 in core draws, four objects for easy/medium and six for
hard, and three foreground colors when feasible.

**Prior choice reversed.** The first repaired version favored width 12 and three
easy objects. With the repeated-color requirement, that combination did not hit
any canonical size/palette profile in the pinned easy 20-draw floor.

**Alternatives considered.** Disable repeated colors on easy; increase the
profile-floor sample; hard-code one canonical draw; weaken the gate.

**Probe.** The new regression samples the exact 20 draws used by the profile
contract and requires an intersection with the four canonical profiles in every
band. It was observed red before the change and green afterward; the final
profile-floor stage and 67-test suite pass.

**Failure modes and limits.** The heavy 10x10 bias intentionally reduces default
canvas entropy to retain canonical support. Broad draws still cover the full
advertised dimension ranges, and final diversity passes.

## D8 — Declare and test both strongest canonical-fitting rivals

**Choice.** Register `fill_bounding_boxes` and `group_by_color` as both canonical
shortcuts and lesson competitors, with `nonrectangle` and
`color_spans_aspects` witnesses.

**Rationale.** Executable rivals convert a review intuition into a source-bound
teaching contract. Both rivals are pure and fit all usable canonical pairs.

**Alternatives considered.** Keep the reasoning only in prose; register only the
prior audit's bbox rival; claim universal identifiability.

**Probe and limitation.** Final semantic battery passes, and the census reports
0 ambiguity across 300 production lessons and 1,200 rotations. This establishes
only finite support against these two declared rivals; undeclared hypotheses and
unmaterialized schedules remain unknown.

## Current native parametric candidate — review-20f27c20b324423a

**Decision.** Keep production v2.0.0 and canonical rule hash `b45100a04df9`
unchanged. Add an opt-in native adapter with `mode=canonical|wide_region_relay`.
The canonical setting returns the selected Racket program byte-for-byte. The
relay setting reuses the canonical aspect classifier as step A on controller
objects, counts the connected color-2 regions created after adjacent differently
colored wide objects merge, and uses that input-dependent count to select the
payload object transformed in step B.

**Why this composition.** Every relay input visibly contains three separate wide
controller objects, while step A can produce one, two, or three connected wide
regions. Therefore the selected payload cannot be determined from the raw object
count or from fixed position alone. The retained `raw_wide_count.rkt`
counterfactual uses the pre-A count of three. On the qualified 30x30 witness the
true intermediate is one, the counterfactual selects payload three, and 79 final
cells differ.

**Episode and export contract.** Both settings use matched deterministic inputs,
2–6 demonstrations, and 1–4 prefix-stable queries. Four private query profiles
include a substantive 30x30 boundary case. Public files are exact-byte hash
named and expose demonstrations plus one query input only; settings, programs,
and query outputs remain private. A strict checker finding during authoring was
fixed: per-turn filenames may not carry an order prefix before the content hash.

**Evidence.** The task-local finite audit covers 64 seeds and both settings (128
episodes), reaches intermediate values 1/2/3, tests the declared rival set, and
executes 30 protected-Racket labels. The example writer executes 14 additional
protected-Racket labels, and all ten saved public files pass independent
structure/identity checks. Native qualification on seeds 0 and 17 passes two
settings × two jobs with three demonstrations, four queries, and 40 protected-
Racket evaluations. The causal helper reports `reviewer_replayed` on the 30x30
wrong-intermediate case. Exact paths are under `checks/67ec1565020d/`; the source
inventory is `workspace/parametric/evidence/manifest.json`.

**Limits and next action.** The finite named-rival audit is not universal
identifiability or evidence of measured training value. Reviewer qualification
is not owner acceptance. The next action is exact integrated-source owner replay,
semantic assessment of the A→intermediate→B dependency, fresh native
qualification, and acceptance if those checks pass. Training admission remains a
separate downstream decision.
