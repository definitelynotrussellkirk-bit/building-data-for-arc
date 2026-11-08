# Working notes: 28ba67946524

## Current repair — version 3.1.0

Assignment `review-f56261b9e2736488`. Current generator SHA-256:
`02f04089533abeaf000d8492f2b9d783cbb016e5e6553694f1ad96d3f68d62a0`.
Canonical rule hash `88eede4e9a69` and all Racket authority bytes are unchanged.

### Defect and root cause

Version 3.0.0 distinguished seven declared rivals but every canonical pair and
all 6,000 generated samples in a three-band census also matched a plausible
stronger shortcut: paint every non-seed endpoint of a two-edge walk, even when
that endpoint has a shorter path from the seed. The branch four-cycle contained
true distance-two targets but no node exhibiting “two-edge reachable yet shortest
distance one,” so the curriculum did not actually teach the word *shortest*.

### Repair

The odd-index branch retains its two true targets and four-cycle, and adds one
bottom component touching both the blue seed and bridge. This seed-adjacent
triangle creates a lawful non-target endpoint of a two-edge walk whose shortest
distance is one. The executable `two_edge_walk` rival, the
`shorter_two_step_endpoint` witness, and their lesson/canonical declarations now
make that distinction source-checkable. Version advanced to 3.1.0.

The sampler was already period two but did not declare its period, which blocked
exact semantic schedule enumeration. `LESSON_SCHEDULE_PERIOD` now derives from
the two schedule profiles; generation uses the same declared value. The reusable
curriculum probe now reports the actual declared-rival names/count dynamically,
so future additions cannot leave a stale hard-coded “seven rivals” label.

### Verification retained

- Focused task tests: 33/33 green, including a red→green shortest-path regression
  in every difficulty band and a regression for dynamic rival reporting.
- Independent census: 6,000/6,000 unique generated inputs; all 3,000 branch draws
  fire the new witness and disagree with `two_edge_walk`; 240 four-pair windows /
  960 rotations have no declared ambiguity.
- Racket semantic gate: 600/600 strict draws, 6/6 witnesses, 6/6 rival claims,
  12/12 lessons identifiable and 0/48 rotations ambiguous; exact period-2 schedule
  enumeration completes. All four canonical-fitting shortcuts are refuted by
  declared generated witnesses.
- Random four-query episode: 3 demonstrations + 4 distinct queries, 7/7 Racket
  labels match an independent pixel oracle.
- Boundary four-query episode: exact 8×10, `chain_len=6`, `n_distractors=4`,
  7/7 distinct labels match the oracle; every branch pair fires the new witness.

### Current limits and disposition

This remains a deliberately narrow family of paths plus one branched-cycle
motif. It does not cover arbitrary contact graphs, multiple seeds, holes, empty
target outputs, larger target sets, or undeclared hypotheses. The production
schedule guarantee assumes consecutive accepted indices; downstream reordering
or rejection must rerun `lesson_identifiable`. Changed source bytes invalidate
the prior approval receipt, so this return needs owner review before admission.

## Prior reviewer considerations (version 3.0.0)

Prior source SHA-256: `44b61d99e1b7418d5b2491f8367a9968afe955982bff04c25e387bcb27741f2a`.

# Prior decisions — 28ba67946524, version 3.0.0

## Scope and authority

Assignment `review-f2e0fbc3f81b1755` stayed fixed. Only the selected task's
generator, documentation, tests and workspace changed. No Racket source,
canonical example, frozen fixture, audit-target source, catalog approval or
shared source changed. The baseline had no task-associated prior return; the
empty associated-note index supplied no additional evidence. The baseline code
itself is the basis for all before claims, not a pending external repair.

Baseline generator SHA-256:
`594f4be2701f07384bafd3e03c42cf4acd1cae93413593b54bd27c0e09de326f`.
Final generator SHA-256:
`44b61d99e1b7418d5b2491f8367a9968afe955982bff04c25e387bcb27741f2a`.
Active canonical rule hash: `88eede4e9a69`, unchanged and now explicitly pinned.
The authority audit records a pre-existing divergent archival source; it was
not substituted for the active canonical rule or silently rewritten.

## D1 / F2 — teach graph distance rather than a single chain position

Observed baseline: all 3,000 draws in the retained Python census had one target
and no reachable cycle. The original rationale is unknown; a line of rectangles
is a cheap constructive realization, but it cannot teach multiple shortest-path
targets. Three plausible shortcuts fit all three usable canonical pairs: select
color4, select the first target only, or merge disconnected equal-color objects.

Repair: alternate varied path examples with a small branched four-cycle. The
branch's two target components have different colors, a disconnected component
reuses one target color, and the bridge is two cells wide before rotation.
This forces whole-component distances and separates eight-connectivity from
cardinal contact. Nonseed colors include8, and8 varies between bridge and target.
Seven executable rival predictions and five actual witness predicates encode
these distinctions. They are diagnoses, never exported training labels.

Rejected alternative: random general graph generation. It would need a larger
embedding/placement system and could silently lose the witness through retries.
Rejected alternative: merely increasing objects or adding color noise. Those
changes can leave the same single-target shortcut intact. A deliberately small
constructive contrast is more auditable, but is not full graph-distribution coverage.

## D2 — exact controls, domain coverage, and canonical support

Retain four axes: grid_h8..18, grid_w10..20, chain_len3..6, n_distractors1..4.
Every difficulty/profile admits the full legal range. Difficulty changes sampling
weights only. `chain_len` remains the backbone's edge count and is also the maximum
reachable graph distance, so it is recoverable from pixels even in branched cases.
`n_distractors` is the count of unreachable connected objects, not unique colors.
Unknown controls and noninteger/out-of-domain values raise explicit errors;
None retains GenCtx's default/no-override meaning. No combination is declared
incompatible. Constructive bounds allow even 8x10, distance6, four distractors.

A reserved spaced row gives guaranteed distractor placement; relocations and
safe growth randomize it without losing count. Rectangles vary in width/height,
translation and reflections/transpose. Repeated colors cannot fuse adjacent
nodes because colors on every intended edge differ.

Path draws strongly favor canonical dimensions and a small palette; they do not
paste frozen examples. The independent 1,000-draw/band profile hits changed from
242/13/0 (easy/medium/hard) to278/279/276. The separate required 20-draw/band
profile gate has9/4/5 exact hits. These are different experiments and denominators.
Strict semantic support is not the same as exact canonical-profile frequency.

The advertised override battery accepted31,140/31,140 draws across346 cases,
three bands and retained per-case seeds, with no finding. Focused tests separately
check all32 joint boundary/profile cases per band, not just one axis at a time.
This is extensive finite checking plus a constructive argument, not exhaustive
sampling of all seeds or a proof that arbitrary external inputs are supported.

## D3 — actual lesson policy and query rotations

Three demonstrations followed by one query is the evaluated production policy.
Even sample indices are paths; odd indices contain the contrastive branch.
Any three consecutive accepted indices include an odd witness. A four-pair
consecutive pool has two odd inputs, so every single holdout leaves at least
one witness in its remaining three demonstrations. Input order does not affect
the component rule; the schedule is for assembling sufficiently informative lessons.

The public Racket-backed census actually materialized100 lessons per band,
300 lessons /1,200 unique input grids overall. Production:0 ambiguous lessons;
all1,200 single-query rotations:0 ambiguous. No materialization, scoring or hook
errors were recorded. The small required-rotation semantic battery also passed.
Evidence contains source hashes, accepted indices, replay seeds and per-rival
results. These conclusions cover seven distinct declared hypotheses, not every
possible inferred program or a measured small-model training improvement.

The Python workspace probe additionally checks20 seeds x3 bands x4 starts =240
overlapping four-pair windows and960 holdouts. It uses independent Python labels,
not the Racket authority, and its windows are not960 independent lessons.
Rejections, nonconsecutive subsets, or deleting additional demonstrations can
break the schedule premise; downstream assembly must run `lesson_identifiable`
on its actual labels. No two-guess scoring argument replaces teaching support.

## D4 / F1 — preserve lawful input8; do not optimize the generator for a false alarm

The main final battery has11 green stages and one failed strict defect-lint stage.
Its only warning says output8 is globally new on15/60 generated pairs instead
of every canonical training pair. Input8 is lawful and is intentionally frequent:
753/1,000 draws per band contain it. Correct painting can reuse an existing color.
The Racket smoke test actually fires on120/120 draws; labels are not no-ops.

Rejected alternative: forbid or sharply suppress input8 until the linter turns
green. That would weaken the intended distinction and contradict canonical
support. The separate generic patch under `checks/optional-tool-fix/` checks
actual changed-cell painting rather than palette novelty alone. It has a real
red/green test history and a clean 60-draw strict integration run. It remains
outside the allowed task delta, so the maintainer must approve that shared
change or explicitly accept the known false-positive warning. Main acceptance
is therefore **needs attention**, not an unqualified green battery.

## D5 — validator and source-bound evidence

The generator validator rejects ragged/noninteger/out-of-range grids, absent or
multiple blue components, and no distance-two target. It accepts legitimate8
objects and repeated disconnected colors. This is an input-distribution validator,
not a complete validator for the full Racket rule's lawful manifold; in particular
empty-target and multiple-source scenes are intentionally outside this sampler.
The no-target restriction makes visible lessons informative; broader empty-output
teaching would require a separately audited curriculum, not a stealth rule change.

Task tests use public portable canonical helpers, not fixed parent-depth guesses.
The reusable census independently rederives graph statistics from returned pixels,
and iterates actual rival declarations rather than a copied name list. Source
hashes, commands, failed iterations, solve provenance and fresh-application receipts
are retained. Optional-tool passes are explicitly separate from main-source passes.

## Self-review for new shortcuts (two sentences)

The repair replaces one path shortcut with an auditable but still narrow family:
reachable outputs contain one or two target components and branches use one four-cycle,
so it does not train arbitrary graph topology, holes, or larger target sets.
Within that stated family, varied orientation/geometry, repeated colors, moving8
roles and retained contrastive witnesses defeat the seven tested rivals; all other
hypotheses and downstream model gains remain unmeasured.
