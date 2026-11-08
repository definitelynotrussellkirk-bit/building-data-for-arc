# Working notes: fae242ae157d

## Current native parametric review — 2026-10-24

The separate `workspace/parametric/` family now supplies a thin native adapter,
promotion contract, exact canonical Racket source, matched sampler, executable
rival audit and two reusable counterexample tools. Production version 4.1.0 and
its source hash `2cc4c3997a0cebffdc3b6c25d6bdf5598f9f5811ede610d1a805b4b0b73a9f70`
remain unchanged. The selected rule is `ce7e86577c99`; its exact program SHA is
`ce7e86577c9974e15935224c415054977e6b7ffb2d2a5d712842ed39b1dff1e4`.

The episode-fixed `ranking_policy` is `area` (exact default), `nearest_largest`,
or `farthest_largest`. Alternatives first identify the uniquely largest object
by occupied cell count, then measure minimum cell-to-cell Manhattan distance
from its cells to each remaining object. The anchor becomes 4; near-first or
far-first order assigns 2/3. This makes the selected object's identity and cells
an input-dependent intermediate required by the spatial comparison. Wrong
bounding-box or fixed-position anchors change outputs. Distances and area ranks
are unique on the admitted shared grammar; no hidden tie convention is taught.

The new sampler supports 3–6 demonstrations and 1–4 queries independently. Full banks and
setting-independent SHA-derived RNG streams preserve exact count prefixes and
matched inputs across policies. The family extends production's fixed dimensions
and 3–12-cell object bound: queries include 9×11, 18×24, 24×24 and 30×30 (rectangles
may be rotated). The 30×30 scene contains 370–450 occupied cells, spans all four
boundaries and produces a 30×30 answer. The exact default reference already
supports those dimensions. Production acceptance and domain are not widened.

Three constructive demonstrations are retained. A metric-conflict line placement
rejects Euclidean and Chebyshev distance: the true distances 6/7 have squared
Euclidean 36/29 and Chebyshev 6/5. Four executed precursor witnesses retain the
original authored 3-demo lesson and a 21-cell query disagreement; this is authored
curriculum evidence outside the old production dimensions, not a saved canonical
ambiguity. See `checks/fae242ae157d/distance-lesson-final.json` in the return.

A first generated audit found a top-left-distance survivor at seed 0, but it agreed
on all four sampled queries. A separately authored rotation of one saved query
then gave a 67-cell disagreement under each distance policy; the frozen original
lesson and executable rules are retained in `top-left-lesson.json`. The fix
selects the first demonstration's symmetry to preserve a top-left-metric conflict,
and selects the second's symmetry so the largest object is neither the first nor
last scan object. This is bounded selection among eight scene symmetries, not
query-based teaching or rejection of whole lessons. Remaining demonstration and
query symmetries vary independently. The final finite audit refutes every tested
rival on the first three demos, including the observed survivor.

Final focused validation: 48 tests pass. The final audit succeeds for all 6 jobs
(3 policies × seeds 0/17), verifies 42 intended labels and 4 official pairs, and refutes
all 122 episode/candidate comparisons using demonstrations only. It uses 280
protected Racket evaluations, 132 cached results and 24 strict one-query public
files. Private answers, settings, programs, seeds and future queries never enter
those public views. The identity rival's initial bare-body wrapper error and the
top-left demonstration regression are retained as failing-first evidence.

These finite results cover the tested sources, seeds and declared rivals. They
do not establish uniqueness against arbitrary programs, unconstrained scene
sampling, measured learning gain, owner acceptance or training admission. Native
qualification and the causal replay bind the exact final adapter/source inventory;
owner integration, exact-live-source qualification and acceptance remain the next
handoff. Historical production decisions below remain unchanged.


Native qualification subsequently passed all 6 jobs with 78 protected Racket
evaluations. The two native causal cases substitute a bounding-box-selected cell
set only for the distance reference, while keeping the true largest object
painted 4. Scores change from 6/7 to 4/0 and 21 output cells change under each
distance policy. The native witness builder and replay passed; source identity
and exact labels are verified, while the causal interpretation is authored.

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-07 review repair (4.1.0)

The 4.0.0 three-slot defaults coupled four observable cues: canonical dimensions,
distinct colours, areas 4/5/6, and ascending scan rank always occurred together;
11x14/rank-permuted always used descending scan rank; and 13x16/monochrome
always used mixed scan rank.  A learner could therefore use dimensions plus
object top-left position instead of comparing areas.

Version 4.1.0 keeps the three-slot semantic lesson schedule but spreads the
observable defaults over a six-slot cue schedule.  Canonical dimensions now
occur with all three scan orders and with generalized area triples; colour
modes recur under more than one scan order.  The old dimensions-plus-position
shortcut is registered as an executable semantic rival and
`schedule_cue_decoupled` is its generated counterexample witness.  Feature-only
coverage predicates are explicitly classified in `BRANCH_WITNESSES`, rather
than being misrepresented as causal rival claims.  Portable regressions require
every length-three demo window to refute the shortcut.

The canonical rule, rule hash, exact overrides, component grammar, strict
fraction target, and canonical acceptance behavior are unchanged.
## Current reviewer considerations

Source SHA-256: `2cc4c3997a0cebffdc3b6c25d6bdf5598f9f5811ede610d1a805b4b0b73a9f70`.

# Decisions for fae242ae157d

## D1 — preserve the selected area-ranking authority

**Choice.** Keep rule hash `ce7e86577c99`: identify exactly three separated
nonzero objects, sort by occupied cell count, and recolour smallest/middle/largest
as 2/3/4 on a zero background.

**Rationale.** All canonical pairs, rule smoke, and authority sync were already
green. The measured defect was in the input curriculum, not the labels or rule.
The historical reason for the exact 4/5/6 canonical examples is unknown; it was
preserved as canonical support rather than treated as the full domain.

**Alternatives rejected.** Changing the Racket rule, narrowing the accepted
grammar to canonical sizes, or changing output colours would have converted a
teaching-distribution defect into an unnecessary authority migration.

**Probe / failure mode.** The final battery again passed rule smoke and authority
sync, and the post-repair visible solve reconstructed the same rule. A future
authority change must update the pin and canonical evidence explicitly.

## D2 — retain a three-demonstration semantic schedule, but decouple exposed cues over six slots

**Choice.** Preserve `EXAMPLES_NEEDED = 3` and the existing semantic profile
cycle, while using a six-slot schedule for scene-profile family and palette
mode. The scan-order cycle remains ascending/descending/mixed.

**Rationale.** Three demonstrations are sufficient when each window contains a
counterexample to the canonical scan/size shortcut. The baseline's semantic
sequence was useful; the defect was that every observable nuisance axis was
locked to the same three residues.

**Alternatives rejected.** Pure randomization would lower but not remove the
probability of an ambiguous window. Increasing the lesson to six demonstrations
would be more expensive and unnecessary. Rejection-sampling complete lessons
would couple pair generation to downstream assembly and hide the source defect.

**Probe / failure mode.** The final cyclic probe checked all 216 combinations of
three bands, 12 seeds, and six starts; every three-demo window refuted the exact
legacy rival. Any change to the period, lesson width, or downstream ordering
requires rerunning this probe.

## D3 — allow generalized area triples on canonical dimensions

**Choice.** Slots using canonical dimensions may draw from the union of the
existing lawful generalized size triples, except the strict canonical anchor
slot, which retains areas 4/5/6.

**Rationale.** In 4.0.0, dimensions alone predicted whether the absolute sizes
were 4/5/6. Reusing canonical dimensions with generalized sizes breaks that cue
without adding a new shape grammar or changing the ranking law.

**Alternatives rejected.** Removing 4/5/6 entirely would weaken canonical
support. Inventing larger or equal-area objects would change the documented
domain or introduce tie semantics. Expanding dimensions beyond the existing
profiles was unnecessary for this defect.

**Probe / failure mode.** The final 180-draw diagnostic observed seven distinct
size triples on canonical-family dimensions, including 4/5/6. Placement remains
bounded by the existing profile geometry; this is not an unrestricted
polyomino/dimension sampler.

## D4 — overlap palette modes across scan orders without making colour answer-bearing

**Choice.** Reuse `distinct` under ascending and descending orders and
`rank_permuted` under descending and mixed orders; retain monochrome examples as
an explicit colour-independence witness.

**Rationale.** The baseline palette mode identified scan-order rank exactly.
Overlapping modes removes that one-step lookup while retaining all three useful
colour regimes.

**Alternatives rejected.** Randomly assigning all modes every time could cluster
within a three-demo lesson. Removing rank-permuted or monochrome inputs would
make colour shortcuts easier, not harder. Permuting fixed output colours would
change the task.

**Probe / failure mode.** The final diagnostic confirms the intended overlaps,
and the semantic gate verifies numeric-colour and identity rivals. Monochrome is
still scheduled only on one scan residue, but dimensions and the rest of the
lesson already refute the joint legacy shortcut; this finite design should be
revisited if new colour-based rivals are declared.

## D5 — make the observed shortcut executable

**Choice.** Add `rank from scene dimensions and top-left position` to
`SEMANTIC_RIVALS` and `CANONICAL_SHORTCUTS`, and add
`schedule_cue_decoupled` as its generated witness in `WITNESS_RIVALS`.

**Rationale.** A prose warning is not replayable. The shared semantic gate can
now verify both facts: the rival fits the canonical examples and generated data
contains a concrete disagreement.

**Alternatives rejected.** Relying only on marginal distribution counts would
not show that a complete lesson refutes the rival. Removing the shortcut from
`CANONICAL_SHORTCUTS` would conceal why generated counterexamples are required.

**Probe / failure mode.** The strict gate checked 60 witness firings and passed;
the larger lesson census found no surviving declared rival. The rival models the
measured failure exactly but does not enumerate every possible composite cue.

## D6 — classify positive coverage as branches, not fabricated rival claims

**Choice.** Declare canonical-anchor, descending-scan, mixed-scan,
distinct-colour, and monochrome predicates in `BRANCH_WITNESSES`. Keep causal
claims only where a named rival must disagree.

**Rationale.** These predicates prove that a feature occurs; they do not each
represent a distinct false rule. The after-phase semantic gate correctly treats
unclassified predicates as weak evidence.

**Alternatives rejected.** Attaching arbitrary rivals merely to silence the gate
would overstate what each predicate proves. Deleting the predicates would lose
useful branch-frequency evidence.

**Probe / failure mode.** A failing-first portable regression requires the five
names to remain branch-classified and disjoint from `WITNESS_RIVALS`. Final
semantic evidence reports five branch witnesses and five verified rival claims.

## D7 — repair task-test portability while retaining frozen fixtures

**Choice.** Use `reviewer_support.find_root`, `canonical_path`, and
`canonical_pairs` in the editable selected-task test file. Do not edit the frozen
root fixture.

**Rationale.** The portable runtime relocates selected tests; fixed
`parents[...] / data/...` guesses fail there. The shared helpers are the
supported source-bound mechanism.

**Alternatives rejected.** Hard-coding another parent depth would merely move the
failure. Copying canonical answers into the test would duplicate authority and
risk drift.

**Probe / failure mode.** The final portable task-test stage passed 22 tests and
recorded copied-source hashes. The audit of `d833a288bd7d` demonstrates the exact
failure mode of retaining a guessed path.

## D8 — support arbitrary single-query holdout for the materialized four-pair lesson

**Choice.** Retain the ordered production policy of three consecutive
demonstrations plus the next query, and explicitly test every one of the four
pairs as the query in the larger census.

**Rationale.** Downstream assembly may rotate the query, and a schedule can look
sound only because one pair carries the sole counterexample. The six-slot
construction was cheap enough to test under both policies.

**Alternatives rejected.** Reporting only ordered-production results would leave
query rotation unknown. Claiming universal identifiability from finite tests
would exceed the evidence.

**Probe / failure mode.** `checks/lesson-census-final.json` reports 0/300
production ambiguities and 0/1,200 rotated ambiguities over 1,200 unique inputs.
This covers declared deterministic rivals only and does not enumerate arbitrary
nonlocal hypotheses or downstream lessons with fewer than three demonstrations.

## D9 — retain failures and avoid approval claims

**Choice.** Preserve the interrupted batteries, strict semantic failures, and
red TDD runs. Report the final source as provisionally reviewed, not as newly
approved or proven to improve model accuracy.

**Rationale.** The failures show that the tests can catch the exact contract
mistakes. Generator review establishes replayable data properties, not training
lift or masked-query correctness.

**Alternatives rejected.** Deleting failed runs would erase causal evidence;
promoting catalog approval would exceed assignment authority.

**Probe / failure mode.** `RESULTS.json` identifies final commands and hashes,
while failed evidence remains under `checks/after/`, `checks/after-final/`, and
`tdd-red-*`. The maintainer still controls admission and approval.
