# Working notes: 2c35533cc389

## Current selected behavior

The selected rule is unchanged: copy the input, collect every red (`2`) source
from that original input, and paint blue (`1`) one column to the right when the
destination is in bounds. A right-edge source writes nothing. A blue write may
overwrite another red in the output, but that overwritten cell still acts as a
source because source discovery precedes painting. The canonical Racket
`RULE_HASH` remains `6c442aca44f9`.

The input grammar is a rectangular 5–8 by 6–10 black grid with exactly 2–8 red
sources. Ordinary samples have no horizontal red-red edge; the overwrite profile
has exactly one. Exact controls are `grid_h`, `grid_w`, `n_cells`,
`right_edge_mode`, and `right_neighbor_relation`. Every three consecutive
production demonstrations visit `anchor`, `edge`, and `overwrite`, so the fixed
three-demo/one-query lesson ordering refutes the declared rivals.

## Review-e61574821ea792ec repair

Baseline generator SHA-256 was
`76079b1a23b06f7ce9b6adc843960003b38d4a65a58242d516dbee9698343dc3`.
The before battery had 11 green stages and one blocking `defect_lint` failure:
93 strict-scalar probes were accepted, including fractional exact controls such
as `n_cells=8.75`, because `GenCtx.draw_int` coerced them with `int(...)` and the
public call arguments were not validated.

Version `3.0.1` adds fail-closed validation for literal integer `seed` and
`sample_index`, nonnegative `sample_index`, the four supported difficulty
values, and unknown overrides. Exact integer axes now use `draw_int_strict`.
The repaired generator SHA-256 is
`e075e2031af5f502ee73f2bdfe45bc044e23ef3f48c1802e9bb1131fd38dd547`.
No sampling schedule, rule mirror, semantic rival, or Racket authority changed.
The minimal reproducer is retained in
`counterexamples/strict_scalar_contract.json`; focused tests cover invalid
scalars, all boundary-axis Cartesian combinations in every band, canonical
parity, source-before-write semantics, schedule windows, determinism, and the
isolated parameter prototype.

## Evidence and limits

The final after battery is 12/12 green. Task-local tests are 132/132 passing.
The larger census materialized 300 production lessons (100 per band, 1,200
unique inputs): 300/300 fixed-order lessons were identifiable against all
declared rivals. Arbitrary query rotation is deliberately **not** claimed:
271/1,200 hold-outs were ambiguous, usually because rotating out the only edge
or overwrite witness leaves `wrap_right_edge` or `only_empty_right` viable.
Downstream data must preserve the generated three-demo/one-query ordering unless
a separately validated rotation-safe schedule is introduced.

No prior return for this selected task supplied a usable repair lead; the task's
associated notes were empty. The packet's baseline interruption during the
first foreground Racket run was infrastructure-only; the unchanged baseline was
resumed to completion before editing.

## Proposed parameter extension

`workspace/parametric/` contains an isolated **prototype** with one episode-level
parameter, `direction = right | left`; `right` is the canonical default. It
executes and retains exact Racket programs for both settings, complete
three-demo/one-query episodes, public challenges without hidden settings or
query labels, and declared-rival checks. It does not alter production generation
or approve the `left` variant.
## Current reviewer considerations

Source SHA-256: `e075e2031af5f502ee73f2bdfe45bc044e23ef3f48c1802e9bb1131fd38dd547`.

# Decisions — review-e61574821ea792ec

## D1 — Keep the canonical rule and Racket authority unchanged

**Choice.** Preserve rule hash `6c442aca44f9`: read every red source from the
original input, copy the grid, and paint blue one cell right when in bounds.
Right-edge sources do nothing; a write may overwrite a red destination without
removing that destination from the original source set.

**Original rationale.** The behavior is stated in the selected source and is
matched by all three labeled canonical pairs. The associated historical notes
file was empty, so any rationale beyond the source comments is unknown.

**Alternatives rejected.** I did not change the Racket program, canonical row,
mirror semantics, colors, or source/write order. The defect was in input-call
validation, not the transformation. Probes: canonical-pair parity and the
adjacent-red witness in the focused tests; Racket rule smoke in
`checks/after/checks/2c35533cc389_after_rule_smoke.json`.

**Failure mode/limit.** A future incremental implementation that discovers
sources after each write would fail the retained adjacent-red regression.

## D2 — Repair the public scalar contract at the source boundary

**Choice.** Add `_validate_call`, reject unknown overrides, and use
`draw_int_strict` for the three integer axes. Increment the generator version
from `3.0.0` to `3.0.1`.

**Reason.** Baseline `defect_lint` found 93 accepted-invalid calls. The minimal
counterexample `n_cells=8.75` was silently converted to 8; invalid seeds,
indices, and difficulties were also accepted. Validation before `gen_ctx` keeps
bad values from being normalized into apparently valid data.

**Alternatives rejected.** I did not round, truncate, clamp, stringify, or merely
warn, because those choices erase provenance and make invalid calls look lawful.
I did not tighten legal integer ranges, so the patch cannot improve tests by
shrinking the supported domain. Evidence: `checks/tdd-red/`,
`checks/tdd-green/`, and
`repo/generators/2c35533cc389/counterexamples/strict_scalar_contract.json`.

**Failure mode/limit.** This task-local repair does not change the shared
`GenCtx.draw_int` behavior for other generators; the audit of `5bf6e2e7ed82`
shows the same class can recur elsewhere.

## D3 — Preserve all five production controls and their support

**Choice.** Keep exact axes `grid_h=5..8`, `grid_w=6..10`, `n_cells=2..8`,
`right_edge_mode=absent|present`, and
`right_neighbor_relation=empty|red`. Preserve sparse ordinary inputs and exactly
one horizontal red-red edge in the overwrite profile.

**Original rationale.** Source comments tie 6×7/6×8 anchors and 4–6 red cells to
the canonical morphology, while medium/hard overwrite slots broaden dimensions
and count. Edge presence teaches clipping; one adjacent pair teaches
source-before-write and unconditional destination painting. Provenance beyond
those comments is unknown.

**Alternatives rejected.** I did not ban right-edge reds, ban adjacent reds,
force canonical dimensions only, or inject fixed canonical examples. Each would
remove a semantic branch or create a memorization shortcut. The 96 boundary
Cartesian cases in the final suite demonstrate constructive support at both ends
of every declared axis.

**Failure mode/limit.** The grammar intentionally excludes dense red bars and
multiple adjacent pairs. Claims outside the documented sparse family remain
unsupported.

## D4 — Treat lesson ordering as part of the production contract

**Choice.** Keep three demonstrations in generated order—`anchor`, `edge`,
`overwrite`—followed by the query. Report arbitrary query rotation as unsupported.

**Reason.** The 300-lesson production census has 0/300 ambiguous lessons, but the
required-rotation census finds 271/1,200 ambiguous hold-outs. Rotating away the
only edge or overwrite witness can leave `wrap_right_edge` or
`only_empty_right` consistent with all remaining demonstrations.

**Alternatives rejected.** I did not claim that a diagnostic green status proves
rotation safety; I also did not add a fourth demonstration or duplicate semantic
witnesses because that would change the existing exporter/training contract and
data cost rather than fix R1. Exact reports are retained through
`checks/lesson-census-compression.json`.

**Failure mode/limit.** Any downstream shuffler or query rotator that ignores the
assembly contract can create ambiguous Qwen training examples despite correct
individual labels.

## D5 — Use TDD and retain genuine failed iterations

**Choice.** Preserve the scalar-contract RED run (18 failures), the missing
parameter-prototype RED run (4 failures), the first prototype schema failure
(1 failure), and the first expanded-suite witness failure (1 failure).

**Reason.** Each failure establishes that the corresponding test detects a real
absence or mistake. The expanded witness was corrected because it accidentally
contained two adjacent pairs and therefore lay outside the generator's stated
grammar; the intended one-pair source-before-write assertion was retained.

**Alternatives rejected.** I did not delete failed evidence, weaken assertions,
or alter production to satisfy an out-of-grammar fixture. Final evidence is
132/132 passing in `checks/task-tests/`.

## D6 — Keep the parameter extension isolated and single-dimensional

**Choice.** Prototype only `direction = right | left`, selected once per complete
episode; retain `right` as canonical/default.

**Reason.** Direction is the smallest coherent parameter that preserves the
family's objects, dimensions, colors, and source-before-write mechanism. It is
visible from complete demonstrations and has an exact executable Racket program
for each setting.

**Alternatives rejected.** I did not combine direction with distance, paint
color, wraparound, or conditional occupancy because multi-parameter variation
would make attribution and lesson identifiability harder. I did not merge the
prototype into production because the assignment approves review of one
canonical task, not a new family. Evidence: `checks/parametric/evidence.json`.

**Failure mode/limit.** The prototype covers two deterministic episodes and one
explicit rival; it is not a proof against all possible hypotheses and does not
claim the left variant belongs in canonical ARC data.

## D7 — Record solve exposure honestly

**Choice.** Complete the unrelated blind solve first, then run the selected-task
solve only after final generator bytes were fixed. Declare the selected solve's
earlier exposure `yes` and reference consultation during the solve `no`.

**Reason.** The visible-only solve is useful evidence about teachability, but it
is not blind after generator review. Both records use one real revision and keep
masked-query correctness unknown.

**Alternatives rejected.** I did not manufacture a failed attempt, call the
post-repair solve blind, or consult private query labels. Evidence:
`solve-blind/summary.json` and `solve/summary.json`.

## D8 — Curriculum annotation: single local rule, no claimed composition axes

**Choice.** Mark multi-rule interaction, sequential state, contextual gating,
and task-defined symbols `not_applicable` for this generator.

**Reason.** The transformation is one local source-to-neighbor paint applied
from a simultaneously captured source set. Source-before-write semantics avoid
sequential mutation; they do not create a sequence of state-dependent steps.
There is no input symbol selecting among rules and no task-defined symbolic
language.

**Alternative/limit.** The proposed direction prototype is hidden at episode
level, not selected by an in-grid context symbol, so it does not justify a
`contextual_gating=present` annotation.

## D9 — Keep adversarial audits separate and do not patch them

**Choice.** Reproduce and report the two drawn audit defects without changing
their source trees.

**Reason.** The assignment requires adversarial review, not repairs, for
`generic_resize_gen3` and `5bf6e2e7ed82`. The first has a Racket-replayed rival
that fits all demonstrations and differs on the query; the second accepts three
concrete invalid calls and emits self-check-clean grids.

**Limit.** The separate `object_count` warning for `5bf6e2e7ed82` was not
investigated deeply enough to classify; `AUDIT.md` labels it diagnostic only.

## D10 — Retain full census evidence losslessly within the return budget

**Choice.** Store the two 11 MB JSON census reports as deterministic gzip while
leaving companion summaries uncompressed.

**Reason.** This preserves every source-bound lesson and failure while reducing
`checks/` from about 27 MB to about 6.4 MB. The manifest records original bytes,
SHA-256, compressed SHA-256, and exact restoration commands.

**Alternative rejected.** I did not delete the required-rotation failure or keep
only aggregate counts. Evidence: `checks/lesson-census-compression.json`.

## Review `review-f7c9403c23453d70` — native directional family

The production generator and canonical rule remain byte-identical. The native
family now exposes episode-fixed `direction_rule = fixed_right | fixed_left |
anchor_inward`; `fixed_right` reads the exact canonical program from
`canonical.rkt`. The sequential setting first counts red sources on both
vertical borders, selects the strict-minority border as `anchor_side`, and then
paints from the frozen original source set one cell inward from that side.

The sampler supports every 2–6 demonstration prefix and 1–4 query prefix on
matched inputs, with four distinct queries and a substantive 30×30 fourth
query. During adversarial review, `topmost_side_inward` survived some two-demo
lessons because random filler was allowed on the top row and could obscure the
constructive cue. Filler is now restricted to interior rows; the mandatory top
cue remains unique. The retained 32-seed audit covers 1,920 episodes, 12,480
labels, and 4,800 public projections with zero findings against the declared
rivals.

Native qualification passes all three settings on seeds 0 and 17 with 60
protected-Racket evaluations. The causal witness uses an input with border
counts 3 versus 1: the intended intermediate is `anchor_side=right`, hence a
leftward paint; forcing the canonical rightward intermediate changes the final
grid. This is finite source-bound reviewer evidence only. Exact integrated-source
owner acceptance, canonical approval of the added settings, and any training
admission remain pending.
