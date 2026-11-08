# Working notes: 2c30a4753f6b

## Intended rule and domain

Preserve the complete input on the left and append its left/right reflection.
The selected Racket authority is unchanged, pinned by `RULE_HASH=692c01024e4b`.
Canonical examples are four 3×3 inputs using colors 0 and 7. The generator's
declared domain is broader: height 1..30, width 2..15, zero as the unique modal
background outside exact public examples, and observable left/right asymmetry.
Profiles select instructional input families; they do not change the output rule.
Outputs remain at most 30×30. The canonical rule is more general than the
generator's intentionally restricted instructional domain.

## Current repair: V3.1.1

Earlier independent profile draws could produce three demonstrations that all
used canonical dimensions or color 7, followed by a query requiring a broader
interpretation. The Racket-labelled baseline episodes at easy seed 1 and seed
639 reproduce this defect; see `counterexamples/baseline_lesson_ambiguities.json`.
Four executable shortcuts fit every canonical pair: reflect only color 7,
repaint the reflection to 7, reflect only the first three columns, or operate on
a fixed top-left 3×3 crop. Duplication and prepending reflection are additional
lesson competitors, but do not fit all canonical demonstrations.

Default generation now alternates a size/color witness at even sample indices
with the full weighted profile mixture at odd indices. Each witness is a 4..6
by 4..6 grid containing two separated, differently colored dominoes, rotated
as a whole. It demonstrates width beyond three, preservation of non-7 colors,
and asymmetry. Three demonstrations and one query are the measured lesson
policy. Explicit `scene_profile` overrides bypass this schedule and retain all
four exact-public and twelve general profiles.

The first schedule repair (V3.1.0) used broad multicolor scenes. Its strict
battery found excess object counts and only 12/60 canonical-envelope hits.
V3.1.1 replaces those witnesses with the small two-object construction and
raises canonical-scale weights in ordinary slots. The final profile check has
19/60 exact/envelope hits: easy 6/20, medium 5/20, hard 8/20. The hard tall
profile also reaches 30×15 inputs rather than stopping at height 20.

Seed must be a literal integer; negative integer seeds remain supported.
Sample index must be a literal nonnegative integer. Boolean, floating, string,
container and null values are rejected rather than coerced. Tests use public
portable helpers instead of fixed filesystem depth or private module imports.

## Evidence and limitations

For final generator SHA-256
`5cfd714cdb89a82d64a954f20b6306d0cc53d8daa9fa862f6df9ba5fdb4f19d4`, the
explicit portable task suite passes 84 tests (49 canonical/contract, 35 prototype).
The production Racket census materializes 300 three-demo/one-query lessons,
100 per band, with 1,064 unique inputs. No declared-rival ambiguity occurs in
300 ordered queries or 1,200 single-pair query rotations. Fixed seed 0 covers
both schedule start residues in all three bands: 6 lessons, 24 rotations,
6 unique inputs, no ambiguity. These are finite measurements, not universal
induction or a proof over all seeds, duplicate-rejection histories, or rivals.
Forced-profile lessons and arbitrary lesson lengths are outside this teaching
claim. Exact receipts are in the review return's `checks/` directory.

The final strict battery passes 11/12 stages. Its remaining warning is
`selfcheck-minimal-impostor`: one of six short-line mutations is accepted as
`near_symmetric`. The retained 4×5 input has exactly one mirrored-cell-pair
mismatch and the reference correctly reflects it to 4×10. This is a lawful
documented profile, so it was not banned merely to satisfy the generic
heuristic. Maintainer adjudication of this shared-tool warning remains needed.
The default witness's recorded construction choice is `multicolor_sparse`,
while the geometry classifier can report `edge_asymmetry` after rotation;
both are lawful, but construction metadata is not always the observed profile.
Explicit override observability remains tested.

## Proposed parametric extension

`workspace/parametric/reflection.py` is a separate runnable prototype with
`axis={horizontal,vertical}` and `side={after,before}`. Parameters are fixed
within each episode; horizontal/after executes the exact canonical program.
It emits three demonstrations and one larger query, executes all labels and
alternate-setting predictions in the protected Racket bridge, and verifies
canonical parity independently. Public challenge files contain only visible
grids; exact programs, parameters, query labels and source hashes are private
authoring evidence. Its verifier checks reexecution, source identity, strict
cell types, public-file inventory and redaction.

The final four-setting emission/replay at seed 20261023 covers 16 labelled
pairs and 12 alternate-setting checks, with no ambiguity. This prototype is
proposed only: no production variant, authority, catalog approval or training
admission is changed. See its README for commands and bounded-domain limits.

Historical imported notes remain in `evidence/associated_notes.jsonl`.

## Current owner source and evidence limits

Accepted3.1.1 strict scalar validation and alternating compact two-color witnesses against six declared size/color rivals, canonical-weighted ordinary profiles and hard tall support. Canonical Racket unchanged. Reviewer84 portable tests pass in authoring and fresh dependency-closure replay; strict battery11/12, with generic short-line warning still failed. Exact lawful4x5 near-symmetric line is Racket-labeled to4x10; this is task-semantic evidence, not a shared exemption. Final300 lessons/1200 rotations have zero declared-rival ambiguity (1064 unique inputs); all period2 starts in three bands give6 lessons/24 rotations, not independent added inputs. One30x15 input yields30x30 output with12 boundary assertions. Metadata construction multicolor_sparse can classify as edge_asymmetry after rotation (104/1000 easy witnesses). Axis horizontal/vertical and side after/before prototype covers4 settings,16 labeled pairs,12 alternative-rule checks; exact canonical default;35 prototype tests. One retained seed plus tests at1729 and construction checks over32 seeds. Separate optional repository suite1002 pass/17 fail/3 skip/18 subtests remains failed, no baseline comparison. Partial replay349/99608 files,10 changed paths; not full extraction. No owner repair battery, production parameter API, variant approval or training admission.
## Current reviewer considerations

Source SHA-256: `5cfd714cdb89a82d64a954f20b6306d0cc53d8daa9fa862f6df9ba5fdb4f19d4`.

# Decisions and evidence

## C1 — Teach the general rule within the episode

The original rationale for independent profile weights is not documented in
the imported current notes. They provide broad individual-input variety, but
do not ensure that three demonstrations establish the intended rule before a
query needs a new size or color. Exact baseline Racket episodes at easy seed 1
and seed 639 show this distinction. At seed 1, three 3×3 demonstrations admit
a fixed-width-three rival before a 13×5 query. At seed 639, all demonstrations
use colors 0/7 before a query with color 4. Labels are correct in both cases;
the defect is teaching sufficiency against plausible canonical-fitting rules.

The retained Python-only baseline probe covers seeds 0..3999, easy,
requested start 0, three distinct demonstrations and one query, skipping
duplicate inputs. It reports 352/4,000 width-three ambiguities, 340/4,000
fixed-3×3 ambiguities and 15/4,000 for each color rival. These are mirror-based
population observations, distinct from the two independently Racket-verified
episodes in `checks/canonical-analysis/verified-counterexamples.json`.

The final choice alternates a compact size/color witness and an ordinary
draw, with period two and `EXAMPLES_NEEDED=3`. Two witnesses in a usual
four-pair window leave one in the demonstrations after any single-pair query
rotation. Actual sampling can reject duplicates, so this informal argument
is supplemented by the production sampler's accepted-index census and an
explicit ambiguity-checking hook; it is not asserted as a proof for all seeds.
All six executable competitors are retained, with four declared separately
as canonical-fitting shortcuts. Authority labels always come from the
selected Racket rule in the production census.

Alternatives rejected: relying only on single-grid witness frequencies;
changing the canonical outputs; exposing parameter labels to the solver;
claiming uniqueness against unspecified programs; or assuming consecutive
indices when duplicate rejection can advance sampling. Forced profile
overrides remain available but bypass the default curriculum and its lesson
claim. The measured policy is three demos/one query, ordered production plus
all four single-pair holdouts preserving remaining order.

## C4 — Preserve canonical scale while adding witnesses

V3.1.0 used existing broad multicolor profiles at witness positions. Its
47 focused tests and finite lesson checks passed, but strict battery checks
reported excessive object count and only 12/60 canonical-envelope hits.
That measured failure caused the revision, not a desire to change random
seeds until a gate happened to pass. The final witness uses two separated
dominoes on a 4..6 by 4..6 field: four colored cells, two objects, two colors,
width beyond three, and observable asymmetry after rotation. The ordinary
mixture increases the public, sparse/dense 3×3, and singleton weights threefold.
This yields 19/60 exact/envelope hits under the prescribed final profile test.

The original full profile list and exact override behavior are retained.
The general hard size cap expands from height 20 to 30; hard tall scenes can
use width 15, allowing 30×15 inputs and 30×30 outputs with actual foreground
content. Easy/medium tall bounds retain their prior limits. We did not add a
scale parameter to the rule: size variation is an input-distribution axis.

The default small witness is intentionally not difficulty-scaled. Difficulty
still changes the ordinary profiles. Two-color dominoes introduce a bounded
construction regularity; the finite evidence does not imply arbitrary
out-of-distribution induction. Observed geometry may classify an edge-only
rotated witness as `edge_asymmetry`, despite the construction choice name
`multicolor_sparse`. This does not alter its colors, width, lawful status or
rival-refuting behavior; construction choice and observed profile are documented
separately, and every explicit profile override remains observable.

## C2 — Scalar API

Accept literal integer seeds, including negative integers, and literal
nonnegative integer sample indices. Reject Booleans, floats, numeric strings,
null and containers before constructing the keyed context. Silent coercion
collapses distinct API requests and hid invalid inputs. New regressions were
observed failing before this repair; final portable tests pass.

## C3 — Test portability and environment

The first isolated task-test attempt was blocked by a missing pytest
dependency. After creating the task's own environment, preflight exposed a
fixed-depth canonical path in the selected task-owned legacy test. Source
mapping confirmed this was the editable task test and that its identical
legacy mirror was omitted by identity, not an independent frozen root fixture.
Only the allowed task source was migrated to `reviewer_support.find_root`,
`load_selected_generator`, `canonical_path`, and `canonical_pairs`; the original
22 test assertions were retained. No frozen root fixture was rewritten.

Both infrastructure/preflight failures are retained separately from executed
test failures. Final selected tests run in a staged portable runtime with
user-site imports disabled and the same Python interpreter for wrapper and
payload. General root pytest does not replace this explicit task suite.

## P1 — Parametric extension first, separate from canonical repair

Axis and placement are small transformations of the original whole-grid
reflection relationship. Their cross-product has four settings, with exact
canonical horizontal/after default. Parameters are fixed for a complete
episode. The query exceeds demo sizes; four distinct corner colors ensure
both-axis asymmetry, avoiding accidental equivalence between settings.

Rejected alternatives include object-selection/recoloring variants that
would introduce a different reasoning task, varying parameters within one
episode, Python-manufactured reference labels, and giving private programs or
parameters to the solver. Actual protected Racket execution supplies every
saved label and alternative-setting prediction; a separate Python mirror is
only a parity check. Canonical `Catalog.apply` independently validates the
default. Exact rule text/hashes and source/runtime hashes are retained.

The prototype deliberately has a broader transform domain than its sampled
episode distribution. Horizontal inputs allow height 1..30/width 1..15;
vertical inputs allow height 1..15/width 1..30. The episode constructor uses
3..15-dimensional inputs so all alternative settings are lawful on a common
sample. Approval and training admission are unchanged.

Independent review found false semantic metadata could pass verification.
Additional tests also reproduced Boolean/float equality holes, extra public
file acceptance and a verification receipt path that could leak answers.
All observed reds remain in `checks/parametric/`; the final 35-test prototype
suite fixes these cases. Earlier successful emission is explicitly superseded.

## F1 — Keep lawful grammar and report the strict blocker

The final generic minimal-impostor probe flags one short line accepted under
the existing `near_symmetric` grammar. The independent exact-probe reproduction
checks 30 mutations across six easy generated grids and obtains the actual
canonical Racket result for the accepted 4×5 input. It has exactly one
left/right mismatch and is a useful reflection witness. The final rule output
is correct, and no authority change is justified.

We retained the lawful input and the blocking warning. A blanket short-line
ban would alter the instructional domain merely to satisfy a generic
heuristic; a silent local/shared exemption would hide the decision. The
maintainer must adjudicate evidence-based exceptions in the shared detector.
No shared tool or threshold was changed. This is why acceptance is explicitly
`needs attention` and the strict aggregate result remains failed.

## Scope and handoff

The packet was safely extracted into an isolated directory; it has no Git
metadata. Its immutable baseline and official builder define the delta.
Only allowed selected-task source and review evidence/reports were changed.
Both assigned audits are findings-only. The final response is the official
small ZIP, with exact failed and successful receipts, solved-example records,
compressed census restoration metadata and a fresh-checkout replay.
