# Current notes: d89cff1052a2

## Rule and selected-source proposal

Canonical authority: `(rule! (vconcat (flip-ud g) g))`, unchanged.
`RULE_HASH = "370a7fcc45fc"`; full source-text SHA-256:
`370a7fcc45fc7aaa55d1ccf5d6310e394cd48e2d23ad55475e0eff5c2e63e389`.
Proposed generator version **2.0.2**, source SHA-256:
`955c103576a5e4b9ec1985adb26fc9dbae6b64d031ccfbde042dcdd5f49cc7a4`.
The five canonical inputs are 3x4 with two colors. Their authority mirrors the
entire input above the original; fixed-three-row reflection is a shortcut.
This reviewer return does not update catalog approval or training admission.

## Current distribution and controls

Exact controls remain `grid_h=3..15`, `grid_w=3..30`, `palette_size=2..4`, and
boolean `ud_asymmetric`. Non-None explicit overrides bypass the ordinary
height-parity schedule and retain the complete prior valid domain. Unknown
controls, invalid scalars/bounds, negative indices, and unsupported difficulties
are rejected as before. `None` overrides mean unspecified.

Ordinary draws use `LESSON_SCHEDULE_PERIOD = 4`:

| Raw index modulo 4 | Input family |
|---|---|
| 0 | Canonical-profile 3x4, two colors |
| 1 | Broad input, even height in 4..14 |
| 2 | Canonical-profile 3x4, two colors |
| 3 | Broad input, odd height in 5..15 |

Half the raw draws therefore retain canonical-profile anchors. Existing
band-weighted defaults are retained within the permitted parity. Broad shapes
use sparse patches, two to four colors, and at least two cells of every color.
The structural validator and exact-control observer are unchanged. Ordinary
inputs remain vertically asymmetric; symmetric inputs are explicit diagnostic
overrides and cannot alone teach reflection versus duplication.

## Reversal: raw alternation did not survive duplicate removal

Prior v2.0.1 source
`14011768b609cdf2cacb79228b2e0d5fe0326d9dddc1fc9335510e6d4e660cce`
alternated 3-row anchors and arbitrary 4..15-row broad inputs. Its previous
repair had correctly excluded height 3 from broad slots, but raw alternation
was insufficient once the worker removed duplicate pairs.

At easy seed 43514, raw indices 1 and 3 are identical 5x8 inputs. The public
Racket-backed worker accepts [0,1,2,4], heights [3,5,3,3]. Holding out the sole
broad pair leaves only 3-row demonstrations. The fixed-three-row rival fits
those demonstrations and returns 8 rows where the reference returns 10.
`counterexamples/duplicate-rejection.json` retains exact pairs and outputs.
The full baseline reproducer, hashes, search range, and baseline source are in
this return's `checks/canonical-review/`.

The new parity-separated broad slots prevent this failure without changing
label semantics or shared deduplication. Any four raw slots contain two broad
inputs with different heights; neither can duplicate the other or a 3-row
anchor. Both must survive into the first four accepted pairs. Every single
query holdout therefore leaves at least one full-height witness. Canonical
anchors may duplicate, so accepted lessons have **at least two distinct broad
inputs**, not necessarily exactly two anchors and two broad inputs. The proof
covers ordinary generation and duplicate rejection, not arbitrary filtering,
subsampling, or overridden curricula.

## Semantic contract and verification

`non_three_height` refutes `fixed_three_row_mirror`; `visible_flip` refutes
`duplicate_input`. Both remain declared lesson competitors. `EXAMPLES_NEEDED=3`
remains unchanged. These finite named rivals do not establish unique induction
against all conceivable rules.

The new 28-case schedule suite failed on the baseline (3 failed, 25 passed)
and passed after repair together with the 42 inherited canonical task cases.
The final isolated task suite has **98 passing cases**: 42 canonical, 28
accepted-schedule, 28 parametric. Its evidence is `checks/task-tests/`.
The final twelve-stage strict battery is green in `checks/after-final/`.
Canonical exact/envelope support is 31/60: easy 11/20, medium 11/20, hard 9/20.

The source-bound final census materialized 300 lessons (100 per band), with
0 production ambiguities and 0/1200 ambiguous query rotations against the
named rivals, across 1197 unique inputs (`checks/lesson-census-after.summary.json`).
Fixed-seed enumeration at the prior failing seed 43514 covered all four starts
in all three bands: 12 lessons, 48 rotations, zero ambiguities
(`checks/schedule-census-after.json`). This evidence was supplied explicitly to
the final battery. The initial after warning about missing schedule evidence
is retained in `checks/after/`; no checker threshold was weakened.

## Proposed parametric extension and reusable authoring tool

`workspace/parametric/` contains a separate unapproved prototype with two
fixed-per-episode parameters: vertical/horizontal reflection-and-join axis,
and reflected-first/original-first order. The vertical/reflected-first default
preserves exact canonical Racket bytes. Complete episodes use common lawful
support, three distinguishing demonstrations, and a larger 15x15 query.
Separate axis-specific boundary probes produce 30x30 outputs.

`racket_episode.py` is a reusable local Racket labeler and finite-rival scorer
for arbitrary labelled episodes and candidate program maps. It verifies labels,
checks all query holdouts, retains ambiguity witnesses, and fails closed on
runtime errors. Public challenge files whitelist demonstration labels and query
inputs; hidden parameters, programs, and query labels remain private.

The final prototype evidence is `checks/parametric/evidence-final/report.json`:
24 episodes over seeds [0,1,17,73,43514,20261022], 96 rotations, all three
parameter rivals refuted, five canonical labels verified, four 30x30 boundary
outputs, and two deliberately ambiguous diagnostic fixtures detected. These
are proposed variant checks, separate from canonical approval. The prototype
uses the included executor adapter and requires its documented runtime.

## Current findings and limits

The assigned task's incoming review index contains no unresolved audit rows.
The duplicate-rejection issue found here is repaired in this proposal. Audit
findings for the two separately assigned targets remain with those targets and
are not resolved by this repair. No shared runtime, canonical source, catalog,
or frozen fixture was changed. Maximum canonical input height 15 follows from
the 30-row output bound; exact 30x30 canonical inputs are unsuitable. No model
score, hidden-solve correctness, training admission, or universal seed/rival
coverage is claimed. Prior exposure is disclosed in the post-repair solve.

## Current owner source and evidence limits

Accept2.0.1->2.0.2 period4 canonical/even-broad/canonical/odd-broad repair for public duplicate rejection at easy seed43514. Every accepted4-pair lesson retains two distinct broad witnesses before holdout. Canonical vertical mirror+original Racket unchanged;exact overrides retain domain. Reviewer reports12/12 battery,98 tests repeated fresh343/96709-file closure,300 lessons/1200 rotations/1197 unique inputs clean;12 failure-seed schedule lessons/48 rotations clean. Initial green battery/census missed rare baseline collision and remain green records. Proposed axis/order4 settings:24 episodes/96 rotations clean,two intentional ambiguities detected. Final receipt distinguishes canonical JSON and raw file hashes. Finite sampler/filter proof,no arbitrary rejection/subsampling guarantee. Owner checked hashes and public/private structure statically; tests and labels remain reviewer-reported.
## Current reviewer considerations

Source SHA-256: `955c103576a5e4b9ec1985adb26fc9dbae6b64d031ccfbde042dcdd5f49cc7a4`.

# Decisions: d89cff1052a2

Assignment: `review-27fc065873ae1c00`; original family `training:4c4377d9`.
The journaled draw and canonical rule were preserved. The inherited approval
and notes from `review-4d6d431a0b1f1d22:v0001` were a lead, not fresh verification.

## D1 — Develop the requested parametric extension first

The selected baseline was already approved and specifically lacked parametric
evidence. The first new runnable prototype therefore varied two small,
episode-fixed rule choices: reflection/join axis (`vertical`, `horizontal`)
and copy order (`reflected_first`, `original_first`). The default is exactly
the canonical rule, including its materialized Racket source bytes. This keeps
the task's reflection, preserved row/column relationships, and concatenation
reasoning recognizable. Input sizes, palette, or density alone would not be
meaningful rule parameters; arbitrary composed transformations were rejected.

The extension lives only in `repo/generators/d89cff1052a2/workspace/parametric/`.
It is a **proposed, unapproved prototype**, with no production parameter API,
canonical authority change, or training admission. See
`checks/parametric/evidence-final/report.json` and the local README.

## D2 — Keep labels executable and demonstrations discriminating

All example labels and candidate predictions are executed through the included
Racket runtime. A Python mirror alone would not establish rule parity. Both
parameters are fixed once per episode; they never change between demonstrations
and query. Seeded parameter choice and seeded input generation use separate
local RNG streams.

Ordinary prototype episodes use three small demonstrations, with shapes 3x4,
4x7 and 6x5, and a 15x15 query. Distinct input shapes prevent pair deduplication.
Every input lies in the common lawful support of all four rules. Both-axis
asymmetry makes copy order observable; output shape distinguishes the axis.
Every single-pair holdout is checked against the three alternative settings.
Axis-specific maximum-input probes are separate: 15x30 vertically and 30x15
horizontally produce 30x30 outputs. Asking all four rivals to execute on those
larger inputs would wrongly treat out-of-domain output sizes as a teaching
signal, so that alternative was rejected.

Symmetric inputs remain lawful. Two deliberately ambiguous diagnostic fixtures
show why symmetric demonstrations followed by an asymmetric query do not teach
copy order. They are negative authoring fixtures, not fabricated failed solves.
The generic local `racket_episode.py` scorer accepts arbitrary labelled episodes
and candidate Racket maps, rechecks reference labels, fails closed on execution
errors, and distinguishes a surviving rival from an answer-changing ambiguity.

The retained evidence covers 24 complete episodes over six explicit seeds and
96 rotations, not all programs, seeds, or input distributions. Prototype input
textures are intentionally separate from the canonical sampler's patch domain.

## D3 — Repair accepted-lesson teaching coverage, not the authority

The initial before battery passed all twelve stages and a fresh 300-lesson
census found no ambiguity. A targeted duplicate search nevertheless found a
real failure at easy seed 43514. Baseline v2.0.1 emits identical broad grids at
indices 1 and 3. The public worker rejects index 3 and accepts [0,1,2,4], whose
heights are [3,5,3,3]. Holding out the sole 5-row pair leaves three canonical-size
demonstrations; `fixed_three_row_mirror` fits all of them but gives an 8-row query
output where the unchanged Racket authority gives 10 rows.

All saved labels are correct and the original fixed-last-query split is
unambiguous. The defect concerns the documented all-query-rotation guarantee.
Exact evidence and baseline bytes are in `checks/canonical-review/`; the
task-owned minimal witness is `repo/generators/d89cff1052a2/counterexamples/duplicate-rejection.json`.

Version 2.0.2 uses four raw slots: canonical, even-height broad, canonical,
odd-height broad. In any four consecutive raw slots, both broad inputs are
different from each other and every 3-row anchor. Both therefore survive pair
deduplication, so every holdout of four accepted pairs leaves a broad demo.
Canonical anchors may still duplicate: **exactly two of each** describes raw
four-slot windows; accepted lessons contain **at least two distinct broad
inputs**. This argument assumes lawful ordinary generation and the current
duplicate filter; it does not promise arbitrary rejection/subsampling policies.

Rejected alternatives were disabling deduplication, fixing the query position,
increasing demonstration count, or changing the canonical rule. Each either
changes shared behavior, weakens the promised curriculum, or changes the task.
The 28 new schedule regressions were run before repair: 3 failed and 25 passed.
They pass after repair together with all 42 inherited canonical task cases.

## D4 — Preserve exact controls and canonical support

Retain height 3..15, width 3..30, palette size 2..4, and the symmetry boolean.
Parity filtering applies only to ordinary draws with no non-None override.
Every explicit override retains its former domain, and half the raw ordinary
slots remain canonical-profile anchors. Broad defaults retain the existing
band-weighted choices within their parity. No new advertised axis is introduced.

The baseline finite joint-control probe covered 8,736 cases. The final strict
battery and canonical tests recheck the changed source; exact/envelope profile
support is 31/60, with easy 11/20, medium 11/20, hard 9/20. Sparse patch structure,
the minimum color count, and diagnostic symmetric override remain intentional.
Inputs larger than 15 rows are unsuitable for the vertical rule's 30-row output
limit; wider inputs up to 30 remain available. No aggregate size quota is claimed.

## D5 — Keep warnings, failures, and approval boundaries visible

The first after battery failed because the new period-four declaration needed
an explicit schedule-census receipt. Its 11 passing stages and warning remain
in `checks/after/`. After the official census enumerated all four starts in every
band at seed 43514, a new complete battery with `--schedule-census` passed all
twelve stages in `checks/after-final/`. The gate was not weakened or patched.

The separate blind solve finished before any generator/rule inspection and
passed 3/3 visible examples in one genuine attempt. The post-repair solve also
passed 3/3 in one attempt, explicitly disclosing earlier exposure. Masked-query
correctness is unknown and neither solve is admitted to training here.

Independent review found no blocking implementation issue. Its minor concern
about canonical JSON hashes versus raw file hashes was addressed in the
prototype receipts and tests. Audit targets retain their selected bytes; their
findings are not repaired or implicitly resolved by accepting this task.

## Self-review and remaining limits

The schedule deliberately correlates ordinary broad height parity with sample
position, but sample position is absent from puzzle inputs and does not change
the transformation. The narrower default distribution is justified by an
accepted-lesson witness guarantee; exact override support remains broader.
Finite named-rival checks cannot prove unique induction against arbitrary
programs. No model training, Qwen9 score, held-out competition score, external
deployment, catalog approval, or shared-tool promotion is claimed.
