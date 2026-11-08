# Working notes: a0fcc6f3396e

## Current rule and source

Version 2.1.0 repairs the input generator under unchanged canonical rule hash
`aadcb1545847`. Three 6×6 panels are separated by full-height color-9 columns.
Each panel contains the four red corners of a rectangle on background 0. Close
rows and then columns, compare the completed shapes up to translation, select
the unique shape, tightly crop it, and recolor the result 8. Two panels have
identical rectangle dimensions and one differs. All three canonical labeled
pairs remain in this family. No canonical or archival Racket authority changed.

## Reversed decisions

The issued 2.0.1 generator advertised controls that it ignored or coerced, accepted
unknown keys, and had no executable teaching contract. Its original rationale
was not recorded. The repair exposes only `odd_panel` (0–2), `rect_h` (2–5), and
`rect_w` (2–6); each names the odd rectangle and is exact, including joint
requests. Out-of-range values, bools, strings, floats, and unknown axes raise
`ValueError`. Fake size, palette, layout, texture, and distractor controls were
removed. Callers relying on ignored controls must migrate instead of assuming
those controls ever changed the grid.

The former validator could overlook color 9 inside a panel even though the
reference uses nonzero cells as markers. The validator now checks the intended
four-corner domain, exact separators, palette, dimensions, and two-matching /
one-odd condition. The wider set of inputs accepted by the Racket program is
not claimed as this generator's input domain.

## Teaching schedule and coverage

Default unoverridden consecutive draws use a deterministic nine-pair cycle and
eight demonstrations. The cycle places each of three shape relationships at
all three odd-panel positions: same height / different width, same width /
different height, and equal area / different oriented dimensions. It includes
both larger and smaller odd rectangles; equal-area cases are nonsquare and
have interior rows and columns. Seeds vary cycle offset, panel permutation,
legal dimensions, and independent placements.

Every nine consecutive default draws contain the complete cycle. Holding out
any single pair leaves examples refuting the 18 declared rivals: three fixed
panels; height, width, and area selectors with each fixed fallback; area extrema;
corners-only; row-only closure; column-only closure; and transposed output. This
is a finite hypothesis check. It is not proof of arbitrary rule induction, and
it does not identify closure order: bounding-box filling and reversed closure
are answer-equivalent on the retained corner family.

Explicit overrides remain lawful and exact, but can replace the scheduled
relationship when required. They do not inherit the default lesson guarantee.
The default schedule deliberately emphasizes diagnostic shape relationships;
it does not sample every legal base/odd pair with equal probability. All 20
original odd rectangle sizes remain supported. `EXPECTED_OUTPUT_CODOMAIN=20`
is derived from this family (4 heights × 5 widths, solid color 8), not from all
inputs accepted by Racket. Difficulty bands share the semantic curriculum;
their seeds vary realizations rather than adding ungrounded difficulty claims.

## Reusable evidence and tests

`counterexamples/same-height-odd-left.json` is a minimal Racket-labeled query.
Always-third and unique-height-with-third-fallback fit all three canonical
labeled pairs but return 3×3 instead of 3×5 on that query. It is a manually
constructed domain witness, not a production frequency measurement.
`tests/test_generator_contract.py` covers that exact witness, canonical support,
all 180 joint band/control combinations, invalid controls, foreign panel color,
all sizes and positions, and cyclic starts / held-out pairs. The return retains
before/after checks and source-bound Racket lesson censuses under `checks/`;
the final acceptance report names the measured counts and current hashes.

## Proposed rule parameter

`workspace/parametric/` is a runnable, task-local output-color prototype for
values 8 (exact original Racket text) and 3. The setting is selected once per
episode, and all outputs and rival predictions are executed by Racket. Public
challenges omit parameter metadata and query answers. This proposal changes no
production API, canonical rule, or training approval. Its tests and evidence
are separate from canonical repair coverage.

## Remaining limits

Untested rivals and arbitrary out-of-family inputs remain unknown. Eight
demonstrations cost more tokens than the former default; the benefit claimed
here is measured witness coverage, not measured model-training improvement.
Downstream users requesting different lesson lengths or assembly policies
should rerun the retained rival census under that exact policy.
## Current reviewer considerations

Source SHA-256: `20ca95cb86ac5682dec158411ede8f77347e6105922a731d612ea2f66cfe39fd`.

# Decisions for a0fcc6f3396e

Assignment `review-97ba56f407991aee`; issued generator 2.0.1, repaired generator
2.1.0. The original task notes and associated-notes ledger did not record a
design rationale, so motivations below are reviewer decisions, not attributed
intent. No pending task-specific review index or inherited task tests were
present. The two random audits were drawn once after the first repair.

## Preserve the intended canonical family

The authoritative program splits on full color-9 columns, closes nonzero panel
cells horizontally and vertically, compares translated shapes, and crops the
odd shape in color 8. The issued generator constructs four rectangle corners
per panel. All three canonical labeled pairs fit that domain. I retained the
6×20 layout, 6×6 panels, marker/background/separator palette, height range 2–5,
width range 2–6, and two-equal/one-odd relationship.

An alternative was to introduce nonrectangular panel patterns to distinguish
row-then-column closure from column-then-row or bounding-box completion. That
would broaden the sampled concept substantially. On four corners these
programs give the same answer, so rejecting them would manufacture a teaching
requirement with no output consequence. The return therefore claims oriented
rectangle selection and completion, not observable closure-order induction.
The Racket text and both authority files remain byte-identical to the packet.

## Replace fake controls with three observable exact controls

The baseline exposed `rect_h` and `rect_w` without honoring them, coerced panel
indices, and accepted unsupported keys. The before override report and 24
failing / 3 passing baseline regressions reproduce this behavior. The repair
advertises only the odd panel and its height/width. A request is validated before
generation and either appears exactly in returned pixels or raises an error.
All 60 joint settings are feasible in each of three bands, so no incompatibility
exception is needed for those controls.

Keeping the old fake axes as no-ops would preserve misleading behavior. Giving
them new palette/layout semantics would alter the canonical family. I removed
them and documented that compatibility change. Booleans and numeric strings
are rejected instead of silently coerced; exact integer controls have a clear
contract. Public keyed draws retain the actual realized dimensions and panel
position, and an independent pixel observer recovers the same values.

## Tighten validation to the generated domain

The baseline validator accepted a foreign color-9 pixel inside a panel while
ignoring it in its own corner interpretation. Racket uses nonzero cells in
that panel, so this was a validator/reference mismatch. The replacement checks
exact separators, legal integer grids, the four corner coordinates of each
rectangle, dimension bounds, and the unique shape. Tests retain the foreign
marker regression and confirm all three canonical labeled pairs remain valid.
This does not claim that every other grid accepted by the general Racket program
must also be admitted by this generator.

## Make the lesson teach the geometric comparison

All three canonical outputs belong to the third panel. A fixed-third selector
and several scalar selectors therefore fit the canonical labels. The retained
manual witness in `checks/teaching-counterexample/run-001/witness.json` uses
canonical demonstrations and a lawful same-height odd-left query: the correct
output is 3×5, while two canonical-fitting rivals return the third panel's 3×3
rectangle. Actual Racket execution supplies the labels. This witness establishes
an ambiguity, not a production frequency; no baseline random lesson rate was
measured for this main task.

I used the existing semantic contract and lesson-census interfaces instead of
inventing a parallel production framework. The repair declares 18 distinct
rivals, with aliases in the supported contract fields. Repeated aliases are
not counted as additional hypotheses. The canonical-shortcut subset contains
only rivals checked to fit all three canonical labeled pairs.

The default nine-step cycle contains same-height, same-width, and equal-area
contrasts, each at every odd-panel position. If a scalar comparison ties and
uses any fixed fallback, at least two positions refute that fallback before
any holdout; removing one still leaves a refutation. At least two smaller and
two larger odd rectangles refute both area extrema after a holdout. Nonsquare
equal-area cases with interior cells refute transpose and incomplete closure.
The phases, panel permutation, and geometry are seeded deterministically.

Eight demonstrations plus one query cover one complete cycle. This consumes
more training tokens, but it gives a direct witness argument across all cyclic
starts and single-query rotations. A shorter schedule covering only one tie
case per scalar can appear sufficient against one fallback while leaving
another fallback indistinguishable. I chose explicit coverage rather than
asserting a smaller lesson is sufficient without evidence.

The measured census checks production materialization, including acceptance
and reference labeling, and then holds out every materialized pair. Focused
tests cover five seeds, all nine cyclic starts, three bands, and every holdout;
they use an independent rectangle oracle. Racket-backed censuses separately
check the reference outputs. The final `REVIEW.md` identifies the final-source
counts, not just passing results from an earlier implementation.

## Distribution limits and codomain declaration

The schedule favors diagnostic relationships, so it does not preserve uniform
sampling over every possible pair of different rectangles. All 20 original odd
rectangle sizes and all three panel positions remain supported. Placements are
independent across panels. Exact overrides are sampled lawfully even when they
cannot honor that phase's teaching relationship; an overridden lesson does not
inherit the default schedule guarantee. Difficulty bands share this semantic
curriculum rather than adding unsupported shape or color variation.

There are exactly 20 possible outputs in the retained family: four heights,
five widths, every cell color 8. The first after check saw 20 distinct outputs
but warned about their repeated frequency. `EXPECTED_OUTPUT_CODOMAIN=20`
records this mathematical family bound and is backed by size coverage checks;
it is not an estimate of the general Racket program's entire codomain. The
repair keeps strict sampling at 100% instead of weakening the strict-profile
threshold to hide a distribution problem.

Self-review: scalar fallbacks are exercised at each position, and equal-area
transpose pairs keep oriented dimensions relevant. A schedule itself can
create untested regularities, so these finite rival results do not certify
universal induction or any Qwen training improvement.

## Proposed output-color parameter

The task supports one small meaningful rule parameter, `output_color` in
literal integers `{8, 3}`. Setting 8 returns the exact canonical source text;
setting 3 changes only the final crop/recolor argument. Inputs remain lawful
corner rectangles and do not depend on the color setting. A deterministic seed
selects the setting once per complete episode. Seed 0 demonstrates 3 and seed 1
demonstrates the original 8.

`workspace/parametric/prototype.py` materializes both exact Racket programs and
calls the bundled bridge for every label and rival prediction. The default
two-seed run executes 24 program/input combinations: two programs on three
canonical pairs, one settings witness, and eight episode inputs. Each episode
has three demonstrations and one query; all three demonstrations distinguish
the output colors. Public challenges contain only visible train pairs and
query inputs. Private evidence retains settings, full answers, executed code,
source hashes, runtime identity, and commands.

This is a **prototype / proposed** extension. It does not modify the production
API, catalog kind, canonical authority, or approval. Independent review found
that a custom seed list covering only one setting could overstate completion;
the status predicate was corrected and its focused regression receipt is
retained under `checks/parametric/review-fix/`. Default two-setting evidence
remains distinct from that additional status regression. Unsupported settings,
arbitrary seeds, and model-training effects remain unmeasured.

## Evidence, failures, and resource handling

Before failures, the first after iteration, successful earlier-source censuses,
and resolved prototype failures are retained. Large prior reports use a
byte-preserving gzip utility already shipped in the packet; its manifest maps
original paths to exact raw sizes and SHA-256 hashes. The return includes the
utility and restore instructions. No failure is discarded to fit the ZIP
budget.

Concurrent disposable runtime copies and a fresh extraction exhausted the
filesystem inode limit. `checks/infrastructure/resource-errors.json` records
the failed commands. I removed only incomplete disposable replay trees and
serialized the remaining runtime work. Final checks and patch replay must be
judged by their completed receipts; an infrastructure failure or an earlier
passing source is never substituted for final-source verification.

## Final execution receipts

The final generator passed all 12 battery stages, 300 production lessons and 2,700 rotations. All 33 portable tests passed and passed again in an independently installed fresh environment. Every changed path matched the exact patch. The fresh replay includes the selected task and all declared runtime/API dependencies; unrelated source homes were omitted after full extraction exceeded inode capacity. See checks/fresh-replay/VERIFIED.json. The final prototype run is checks/parametric/final-run/result.json; earlier prototype receipts remain historical source-bound evidence.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/a0fcc6f3396e/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
