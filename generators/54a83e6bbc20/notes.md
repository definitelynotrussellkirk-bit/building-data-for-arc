# Working notes: 54a83e6bbc20

## Current parametric extension

`workspace/parametric/prototype.py` adds a separate proposed `assembly_order`
setting: canonical `top_to_bottom`, or `bottom_to_top` that reverses complete
assembled bands while retaining each piece's orientation. The variant changes
only the Racket output-origin clause. Generator v4.0.0 source
`cca4fcc91281d89167c1720318f997267741052520e441a5266b17ac11b8b95c`
and canonical authority `82f172ba82d3` are unchanged.

The setting is fixed by seed parity for the whole episode. Independent counts
support 3..32 demonstrations and 1..32 queries, default 3/4, with globally distinct
inputs and explicit bounded failure. All labels execute the matching Racket
program. The first three hard-band samples retain equal-area and row-critical
anchors. Demonstrations filter 19 declared programs, including both orderings of
all six wrong matchers; each query is then checked against surviving predictions.
Query answers never select the survivors. This finite test is not a universal
identifiability or learning-performance claim.

Current evidence: 22 focused tests pass; two retained 3/4 episodes supply 14 real
Racket labels and eight query checks; a 32/32 episode supplies 64 distinct inputs
with matching Racket labels. `verify_semantics.py` checks 24 Racket evaluations
across both modes: all four canonical labeled fixtures, six generated size-boundary
examples, and two counterfactuals. Swapping cyan anchors alone changes the answer
in both modes; swapping candidate locations alone preserves it. Expected grids
are independently reconstructed from row cuts and candidate colors.

Candidate-order assembly was rejected as the extension because a right-piece-only
solver can fill the rest of each rectangle cyan. Reversed cyan order keeps the
anchor dependency. Whole-grid reflection is a distinct rejected rival because
it also flips the rows inside each piece.

Current hashes, commands, rules, examples, and check summaries are under
`workspace/parametric/evidence/` and its manifest. Only `examples/public/` contains
shareable challenges; filenames hash the exact shared visible projection, and
private settings and query answers do not affect IDs. The CLI refuses private
evidence inside the public directory. Tests cover duplicate-export collisions,
reference failure propagation, and sampling exhaustion after the exact budget.

Limits: fixed three-row, width-five shapes; prototype episodes use 17×11 hard
scenes, with semantic checks additionally covering 9×11 and 13×11. Smaller demo
counts, arbitrary shapes, universal teachability, and measured model improvement
are unsupported. This is a proposed variant, with no production parametric API,
new variant approval, or training admission. The next owner action is to review
this separate rule extension and decide whether to expose an episode-level API;
the canonical source does not need a repair from this work.

## Review 2026-10-02 / review-6910db70eef2b3b1

Version 4.0.0 source: `cca4fcc91281d89167c1720318f997267741052520e441a5266b17ac11b8b95c`. Authority hash `82f172ba82d3`, unchanged.

The previous six-cell-only cut bank unintentionally allowed selecting matches
from any two row lengths. Broader palettes/placements cannot repair that. The
new sampler retains equal-area anti-size anchors, adds single-row collision
anchors, and uses other mixed-area draws for variety. All 64 cut vectors and all
32 candidate permutations are supported. It is still a fixed three-row, width-five
jigsaw family, not arbitrary-shape generation.

Shape schedule: every three indices contain equal-area/nonidentity and
row-collision/reverse anchors, plus a variety slot. Seed-fixed critical rows make
query-changing omission rivals visible in the demonstrations. The seven-way
variety schedule gives long-run class weights 3/7, 3/7, 1/7; permutation support is
complete but deliberately nonuniform. Explicit override curricula are outside the
default-window claim. The original non-sorted-color policy remains.

The canonical rule searches for its first rectangular placement and then votes
on width. An exhaustive finite model finds four unsafe four-cut sets with tied
width-four and width-five votes. They are explicitly rejected rather than changing
Racket. Eight real-oracle counterexamples are retained in this review's evidence.

`_placement` is equivalent to the old brute-force target-five search on all 4,096
cut pairs. The intended-rule mirror and actual authority are kept conceptually
separate: validator/generation restrictions make their results agree on the
supported domain.

The 32-value scene enum exceeds the shared override parser's limit. Metadata
marks it manual and names the complete local 96-combination regression rather
than pretending the automatic matrix tests it. No shared-tool patch was made.

Final evidence: 20 task tests, 12/12 battery stages, a 600-draw independent census,
120 sampled generated Racket comparisons, 64 cut-basis Racket comparisons, and
1,095 overlapping finite-rival lesson windows. Full review/commands are in the
return's `REVIEW.md`, `DECISIONS.md`, and `RESULTS.json`. No model training or ARC
benchmark improvement is claimed. Imported historical notes remain unchanged in
`evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `cca4fcc91281d89167c1720318f997267741052520e441a5266b17ac11b8b95c`.

# Decisions and rejected alternatives

All final measurements reference generator SHA-256 `cca4fcc91281d89167c1720318f997267741052520e441a5266b17ac11b8b95c`. See `REVIEW.md` and
`checks/PHASES.json` for the before/intermediate/final source distinction.

## D1 / G1: retain equal-area puzzles, remove a global fixed-sum rule

The original code deliberately chose equal-area shapes to defeat area-only
matching. That rationale is sound, but pinning the area to six globally makes
one of three row lengths algebraically redundant. The original bank contains
only ten vectors. A correct two-row match forces the third row without looking
at it. The before census confirms all three omission rivals at 360/360 outputs.

The repair uses every vector in `{1,2,3,4}^3`. Equal-area scenes still exist, but
choose a feasible area bucket rather than always six. Row-collision scenes use
a base vector plus neighbors that differ in exactly one row. Other mixed-area
sets supply remaining shape variety. All three categories are observable from
the input, and the axis rejects unknown values.

Rejected: use uniformly independent arbitrary shapes only. Such inputs may make
area-only matching reliable and do not ensure demonstrations distinguish the
new row rivals. Rejected: leave area fixed and add only more placements/colors;
that cannot repair the conditional redundancy. Retained limitation: all shapes
are three-row prefixes/suffixes, not arbitrary polyominoes.

## D2 / G2: preserve authority, explicitly bound the enlarged domain

Reading the actual authority revealed a first-rectangle-placement search followed
by a modal-width vote, rather than a direct request for width five. The independent
finite model found no unsafe 2- or 3-piece cutsets and four unsafe 4-piece sets:
679,056 subsets examined in total. The Racket oracle disagrees with the intended
five-wide assembly for each of the four sets in identity and reverse order.
The original validator accepted those eight fixtures; its ordinary generator
never emitted them, so this was not falsely counted as an original draw failure.

Generation now requires width five to have a strictly greater vote count than
any other width. The validator enforces the same restriction. The first-placement
helper uses the actual search ordering and a cached 64×64 domain. Negative
translations cannot produce the required origin-zero bounding box. Cardinality,
disjointness and bounding-box area determine whether a union fills a rectangle.

Rejected: modify Racket to force width five. The selected authority was unchanged;
a task-local distribution restriction suffices and avoids changing reference
semantics. Rejected: silently substitute an easy template on retry exhaustion.
The sampler has 128 bounded attempts and raises if it cannot satisfy constraints.
No such exhaustion occurred in the measured final cohorts.

## D3 / G3: require contrastive demonstrations, not just isolated hard inputs

Initial v4 expanded geometry successfully, but the battery found two ambiguous
lessons out of twelve. The retained examples include an easy lesson with an
area-only survivor and a hard lesson with row-omission survivors. Regression
windows reproduced failures before the fix (`checks/curriculum-red/`).

Every three consecutive default indices now contain (a) a nonidentity equal-area
anchor and (b) a reversed row-collision anchor, with (c) a variety slot. Critical
rows are deterministically fixed per seed: one, two, or three rows for easy,
medium, or hard. Keeping the base piece first while reversing candidate order
makes each active omission rival pick incorrectly on its anchor. Collisions in
other default samples remain on those same critical rows. A rival that survives
all three demonstrations therefore cannot change the following query within
this declared family; the code and regression test embody that finite-rival
argument. The observed evidence is 1,095 overlapping windows and 12 gate lessons,
not an exhaustive enumeration over seeds or all conceivable wrong programs.

Rejected: force every single input to kill every rival. That is impossible for
some small easy scenes and would collapse the distribution. Rejected: repeat one
canonical discriminating input in every lesson. Anchors instead draw fresh cuts
and colors. Limitation: fixed schedule structure is itself learnable; it should
not be used as evidence of distribution-free ARC reasoning.

## D4: complete permutation support without breaking existing names

All original ten scene override names remain valid. The missing permutations get
stable explicit names, giving 2/6/24 permutations for two/three/four pieces.
The variety slot traverses the full permutation set; its seven-step shape cycle
is coprime to all three permutation periods. Two anchor slots plus this variety
cycle yield long-run weights 3/7 equal-area, 3/7 row-collision, 1/7 other mixed.
The final 200-draw-per-band census observed all 32 permutations and all 64 cuts.

The existing rule that excludes globally sorted output colors is retained rather
than conflated with the geometry repair. Its rationale is to defeat a color-order
shortcut. It still restricts color-order support; I do not claim otherwise.

## D5 / G4: be explicit about the framework's enum limit

A computed AXES string first triggered a nonliteral-metadata lint warning. Making
it literal exposed a second issue: the shared parser refuses string domains with
more than sixteen values. The final 32-value domain is complete and literal,
marked `probe: manual`, with the exact test named in `probe_evidence`. The manual
regression tests every one of 96 scene × shape combinations for successful
validation, observed axes and repeatability. A separate test binds literal enum
values to the runtime names, avoiding two drifting lists.

The automatic battery now reports the exemption explicitly and checks the
remaining shape-axis matrix and unknown keys. This is not described as automatic
coverage of all 32 scenes. Shared parser improvements belong in maintainer work;
no out-of-scope edits were made.

## D6: optimize a finite placement check only after differential testing

The Python intended-rule mirror previously searched 77 translations per pair.
It now normalizes the exact missing cells and candidate shape, returning the
unique translation if they coincide. The independent original brute-force test
compares all 4,096 ordered cut pairs. This improves the cost of larger lesson
probes without changing accepted placements. No separate speedup benchmark is
claimed; the result is equivalence coverage, not a measured runtime multiplier.

## D7: reusable probes and exact evidence, not just a review essay

`workspace/run_review.py` stages a clean copied runtime and explicitly includes
new task-local tests omitted by the static runtime mapping. Its census independently
decodes shapes, reconstructs outputs, scores omission rivals, records exact real
Racket witnesses, enumerates first-placement geometry, and saves hashes/commands.
`workspace/audit_assigned.py` runs the two findings-only audits in another copied
runtime and saves exact counterexamples. Both use the selected Racket source.

Intermediate failures and source/test states are retained rather than overwritten.
The final/source distinction is hash-based, not inferred from folder names.
`RESULTS.json` preserves nonzero test outcomes and the actual execution locations.

## D8 / T1: stop at the task boundary, not at the first red result

The full repository suite was run, not only the local tests. Its streaming test
fails before the child prints under the supplied 200 ms timeout. An isolated
retry confirms the failure. A diagnostic with site initialization disabled and
with a longer normal startup budget retains the correct output, supporting an
environment-sensitive test assumption. I did not change the shared runner/test,
mark the suite green, or discard its log. This remains a maintainer issue.

## D9: limits of the delivered result

The Racket basis checks, finite geometry enumeration and deterministic tests do
not prove sample efficiency, transfer to new ARC families, or prolonged training
value. The fresh solve is exposure-contaminated and queries are withheld. Use this
as a repaired component in a varied training mix, with independent held-out
learning curves before assigning it a large training budget. Catalog approval is
not automatically rewritten to approve a new generator hash.
