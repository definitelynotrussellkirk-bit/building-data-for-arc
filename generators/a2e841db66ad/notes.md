# Current notes: a2e841db66ad

## Intended rule

Count every blue (`1`) cell in the top row. In the body, find the unique
four-connected monochrome component whose tight bounding-box height equals that
count. Crop to that component's bounding box and recolor its occupied cells cyan
(`8`). The canonical Racket rule remains the label authority; its pinned normalized
hash is `b5be85c39dab` and was not changed in this review.

## Current generator contract (version 3.0.0)

The generator exposes five exact, observable axes: `height=9..22`,
`width=15..22`, `selected_rows=2..6`, `n_components=3..5`, and
`header_layout=packed_left|shifted_run|scattered`. It constructs separated
components directly, with distinct colors and pairwise-distinct heights, so every
advertised override product is realizable and exactly one component is selected.
Unknown axes, invalid scalar types, negative `sample_index`, and invalid difficulty
values fail before generation.

The default schedule anchors canonical `(height,width,distinct-colors)` profiles at
sample residues 0 and 1. Header layouts cycle
`scattered / packed_left / scattered / shifted_run`. A scattered header has a span
larger than its count and the body includes a component of that span, giving a
defined counterexample to the strongest canonical-fitting shortcut: selecting by
blue span instead of blue count.

## Decisions changed in this review

The prior version treated distractors as optional after failed random placement,
advertised dead or aliased palette/texture axes, accepted unknown overrides, and
emitted no canonical-profile support in the 60-draw floor. Those choices were
replaced with constructive placement, five truthful axes, strict input validation,
and scheduled profile/semantic anchors. Degenerate invalid scenes were removed
from the production axis contract rather than mixed with trainable examples.

Solid cyan outputs remain legal. A selected component can fill its bounding box;
the canonical crop-and-recolor rule then necessarily returns an all-`8` rectangle.
`SOLID_OUTPUT_JUSTIFICATION` records this explicitly.

## Verification and retained evidence

- Final generator SHA-256:
  `12177b6015ccea229498e58e966b638b0a2cb5eda7ba21c9fb3741de9d99d2c5`.
- Focused portable tests: 9/9 pass in
  `checks/task-tests-counterexample-green/`.
- Full after battery: 12/12 green in `checks/after-v2/`; the exact override matrix
  accepted 38,610/38,610 draws with zero findings.
- Canonical profile floor: 27 exact and 29 envelope hits in 60 draws, with support
  in every difficulty band.
- Lesson census: 300/300 five-pair lessons materialized (four demonstrations plus
  one query), 1,500 unique inputs, zero production ambiguities, and zero ambiguities
  across all 1,500 held-out query rotations in `checks/lesson-census-final.*`.
- The retained shortcut probe found scattered-header witnesses on 48/96 sampled
  inputs and zero failures across 120 cyclic query rotations.
- Exact Racket-checked counterexample:
  `counterexamples/blue-span-selects-height.json`, backed by
  `checks/shortcut-counterexample/racket.json`.

## Known limits and open findings

This is a calibrated subset of all lawful rule inputs: 3..5 components, component
heights 1..8, component widths at most 4, pairwise-distinct component colors and
heights, and no tied selector. The finite semantic checks refute the declared
blue-span rival; they do not prove uniqueness against every conceivable induction.
The large random census covers the production sampler and all rotations of each
materialized five-pair bundle, not every seed in the infinite input space.
## Current reviewer considerations

Source SHA-256: `12177b6015ccea229498e58e966b638b0a2cb5eda7ba21c9fb3741de9d99d2c5`.

# Decisions for a2e841db66ad

## 1. Replace the old axis surface with five exact observable controls

**Choice.** Keep only `height`, `width`, `selected_rows`, `n_components`, and
`header_layout`.

**Reason.** The old palette, palette-size, color-count, density, position-bias,
and texture controls were dead, aliased, non-probed, or mixed invalid degenerates
into the trainable domain. They produced 20,669 override findings, accepted an
unknown key, and obscured the actual rule variables.

**Rejected alternatives.** Marking dead axes diagnostic would make lint quieter
without giving callers real control. Declaring thousands of incompatible products
would preserve a misleading API. Retaining `no_header`, `no_matching_height`, and
`tied_heights` as normal texture values would continue emitting inputs outside the
claimed unique-selector task.

**Evidence.** Baseline:
`checks/before/checks/a2e841db66ad_before_override_results.json`. Final:
`checks/after-v2/checks/a2e841db66ad_after_override_results.json` reports
38,610 accepted draws, no explicit rejections, and zero findings.

## 2. Use constructive placement, never optional distractors

**Choice.** Allocate component widths and mandatory blank gaps across columns,
then place each connected shape in its own column interval. Every requested
component is present or generation raises an internal construction error.

**Reason.** The previous random placer ignored a false return for distractors, so
advertised 3–5 components could silently collapse on packed boards. Direct
construction makes component count, unique heights, and exact overrides true by
design.

**Rejected alternative.** Retrying random placement would remain probabilistic
and would need arbitrary retry limits. Treating distractors as pedagogically
optional contradicts both the axis and the lesson contract.

**Probe/failure mode.** The endpoint cross-product test covers both ends of all
numeric axes and all three layouts in every band, including 9x15, six selected
rows, five components, and a scattered header.

## 3. Calibrate dimensions and canonical support

**Choice.** Use heights 9..22 and widths 15..22, and schedule exact canonical
profiles `(9,15,5)`, `(10,16,5)`, `(11,17,5)` at sample residues 0 and 1.

**Reason.** The canonical examples establish a minimum width of 15 and three
profile anchors. Larger dimensions preserve the useful hard-band range while
keeping the full advertised cross-product constructible.

**Rejected alternative.** The former width 10..22 declaration was broader than
the calibrated examples and interacted badly with random packing. Opting out of
profile support would avoid rather than solve the baseline 0/60 profile-floor
finding.

**Measured result.** Final profile floor: 27 exact and 29 envelope hits in 60
draws, with 7/9/11 exact hits in easy/medium/hard and no crashes.

## 4. Make count-vs-span the explicit semantic lesson

**Choice.** Cycle layouts as `scattered, packed_left, scattered, shifted_run`.
For every scattered header, choose a span greater than the count and include a
distractor whose height equals that span. Declare the blue-span rival in
`CANONICAL_SHORTCUTS`, `SEMANTIC_RIVALS`, and `LESSON_COMPETITORS`.

**Reason.** Blue span equals blue count in all three canonical examples, making
it the strongest natural shortcut. A separated header alone is insufficient if
no span-height object exists; the explicit distractor makes the rival produce a
plausible but wrong answer.

**Rejected alternatives.** Always left-packing the header leaves the shortcut
unfalsified. Merely shifting a contiguous run changes position but not span.
Allowing the span rival to raise because no matching object exists is a weaker
teaching signal than a defined disagreement.

**Evidence.** `checks/shortcut-probe-final.json` shows 3/3 canonical fit, 48/96
generated witnesses, and zero failures over 120 cyclic query rotations. The
Racket-checked exact case is retained under `counterexamples/`.

## 5. Require four demonstrations and test every query rotation

**Choice.** Keep `EXAMPLES_NEEDED=4`; a lesson is four demonstrations plus one
query. Use the periodic header curriculum and reject a lesson when a declared
competitor survives all demonstrations but changes the query.

**Reason.** Four demonstrations permit mixed packed, shifted, and scattered
headers while retaining enough object/shape variation. Because downstream code
may rotate which pair is the query, the contract must hold for every holdout, not
only the production order.

**Measured result.** The source-bound census materialized 100 lessons per band:
300/300 production lessons, 1,500 unique inputs, zero production ambiguities, and
zero ambiguities in all 1,500 held-out query rotations. This is finite evidence
against the declared rival, not a proof against all hypotheses.

## 6. Keep lawful solid outputs and document them

**Choice.** Permit shapes that fill their bounding box and declare
`SOLID_OUTPUT_JUSTIFICATION`.

**Reason.** A solid selected rectangle is lawful under the canonical rule; crop
and recolor necessarily yields an all-cyan output. Forbidding it solely to satisfy
a generic heuristic would narrow the domain without semantic justification.

**Probe.** Seed 1002/sample 2/easy produces a nontrivial solid output and is
covered by a focused regression test. Defect lint is green after the explicit
source-bound justification.

## 7. Fail malformed calls before sampling

**Choice.** Require exact integer `seed` and nonnegative exact integer
`sample_index`; require `difficulty` in `None/easy/medium/hard`; validate override
types/domains and reject unknown keys.

**Reason.** Silent coercion or ignored keywords make runs non-replayable and let
typos look successful. The old source generated 136 strict-scalar findings and
accepted an unknown override key.

**Evidence.** Focused tests exercise booleans, floats, strings, negative indices,
invalid difficulties, wrong override types, and an unknown axis; final defect lint
and override stages are green.

## 8. Keep Racket authority unchanged

**Choice.** Add a Python `rule_mirror` for authoring checks, but do not alter the
canonical Racket rule or canonical data.

**Reason.** Rule smoke and authority sync already showed the selected authority
was correct. Generator repair should improve sampling and teaching, not redefine
labels.

**Evidence.** Final rule hash remains `b5be85c39dab`; rule smoke, Racket lint, and
authority sync all pass. Exact shortcut claims use retained `arcpuzzles apply`
receipts rather than the Python mirror alone.

## 9. Retain reusable probes and acknowledge limits

`workspace/shortcut_probe.py` reads live rival declarations, checks canonical
fit, searches generated counterexamples, and rotates queries. It is covered by
the task suite so declaration drift fails visibly.

The current grammar deliberately excludes tied selector heights, shared component
colors, more than five components, heights above eight, and component widths above
four. These are domain restrictions, not claims about the full Racket rule. The
semantic evidence covers one named canonical-fitting rival; future audits should
add new plausible rivals rather than interpreting a finite pass as universal
identifiability.
