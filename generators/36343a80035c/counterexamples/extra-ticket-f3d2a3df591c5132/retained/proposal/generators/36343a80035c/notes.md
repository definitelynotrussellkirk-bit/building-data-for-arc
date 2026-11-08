# Working notes: 36343a80035c

## Proposed v3.1.1: teach the border condition in every example

A user-requested extra ticket retained an ordered seed-17, hard-difficulty
lesson: samples 0..2 are the three demonstrations and 3..6 are four queries.
The executable Racket rival that paints every zero component of area at most
four fits all demonstrations and the first query, but changes queries 1, 2,
and 3 (zero-based). On query 1 it wrongly paints the corner at [0,0]. The
previous lesson gate reports no reasons because that rival was absent.
The fixed source-bound witness is `counterexamples/small-region-ordered-lesson.json`;
its baseline generator hash is
`6da08b295ba2866808f89ba6be339eff2c687a16e13bd52c9d64b58a273dee10`.

The native export was also exercised with its automatic four-demonstration
policy at seed 17, hard difficulty, and four queries. It emitted samples 0..7
with no rejections and passed every declared lesson check. All four demos fit
the size-only rival; its first query (sample 4) is already wrong. The exact raw
export and protected-Racket replay are retained in the extra-ticket evidence.
The export's inherited reviewed-safe label is provenance of the original
catalog state, not a claim that this underidentified lesson is clean training
data. The proposed rival gate detects the native four-demo ambiguity too.

The proposal registers `small_zero_regions` and its teaching witness. After
embedding, if the grid lacks a small border-connected zero region, add two
walls beside an empty physical corner. This makes a singleton border region
that must remain zero. The always-empty base corner, all D4 transformations,
and zero padding guarantee an available inward 3x3 corner. Adding the walls
cannot change enclosed cells, profile areas, or the palette. The broad input
checker remains unchanged; lawful inputs need not contain a teaching decoy.

Version 3.1.1 changes every keyed RNG seed. Consequently, equal seeds across
versions may give different layouts. Exact unchanged-answer evidence applies
to the helper's direct mutation of frozen old inputs, not whole generated
outputs compared across versions. Existing natural border witnesses need no
helper mutation. The new tests retain both the exact old lesson and observable
size/border/axis contracts. This proposal does not claim unrestricted shapes,
larger holes, variable hole counts, arbitrary-program uniqueness, or measured
training benefit. Owner integration/acceptance remains pending.

## 2026-10-02 — v3.1.0 review candidate

The v3.0.0 baseline passes its 12-stage battery but produces only rectangular
holes. In a 600-draw independent census, rectangle-only, hole-bounding-box, and
8-neighbor rivals all match every answer. The first two also fit all canonical
pairs; the third contradicts canonical diagonal-contact evidence.

The candidate keeps four hole-area signatures and the canonical-size anchor,
but non-anchor slots include compact L/T/S zero regions. Cooperative cages omit
redundant corner walls, ensuring a 4-vs-8 connectivity discriminator on every
draw. All old exact overrides and palette groups remain supported. Historical
profile names refer to their area signatures, not literal rectangular geometry.

New witnesses/rivals use the existing semantic gate; `rule_mirror` opts the
Python helper into Racket parity checks. The 600-draw candidate census contains
450 nonrectangular examples and 600 connectivity discriminators. The inherited
semantic gate uses a different off-diagonal census and measures 443/600 and
600/600 respectively. Both are retained, not conflated.

No Racket source or approval metadata changed. Ordinary draws still contain two
small holes in a finite spatial template. Larger holes, counts other than two,
and irregular scene layouts are future work, not claimed coverage. More
canonical support is not equivalent to a training benefit; none was measured.

Reusable tools and fixture tests are in `workspace/`. Reports, failed attempts,
audits, solve declarations, and exact commands are in the source-bound review
return for assignment `review-4acc2985ffffc33e`. Imported associated notes remain
unchanged as historical evidence; they are not overwritten by this entry.
## Current reviewer considerations

Source SHA-256: `6da08b295ba2866808f89ba6be339eff2c687a16e13bd52c9d64b58a273dee10`.

# Decisions — 36343a80035c

## D1: Preserve the rule and semantic palette
The existing rule says all nonzero cells are walls and extracts 4-connected zero
components that do not touch the border. Canonical examples and Racket execution
agree. Background 0 and output 8 are semantic constants, not arbitrary colors.
No Racket repair is justified. Input color 8 remains a useful distractor.
Original rationale is recorded in the imported associated-notes ledger.

## D2: Keep the four lesson slots and area-observable exact axes
Retain area multisets (1,2), (2,3), (1,4), and (2,4), the 9..14 dimensions, all
three palette groups, and explicit rejection of unknown controls. The original
rationale was bounded canonical support and guaranteed rival-killing lessons.
Increasing the demonstration budget merely to add shapes would cost context;
replacing the anchor would reduce narrow canonical support. Historical profile
names remain compatibility identifiers; their geometry is no longer literally
all squares/straight tall pockets. The docstring and axis default explain this.

A consequence worth preserving: only the last three slots can have a
nonrectangular hole. The first two hole areas cannot express one. Therefore the
new rectangle rivals are tested at lesson level and on the non-anchor slots,
not forced to disagree on an impossible anchor. All original rivals remain
required on every ordinary profile.

## D3: Add three compact nonrectangular shapes, not unbounded shape noise
Use an L triomino and uniformly choose an L, T, or S tetromino through a named
local RNG stream. A 5x4 motif including cardinal wall neighbors fits every
existing minimum-dimension override. Two holes, open-U decoys, palette membership,
and area observability are preserved without rejection sampling or retry bias.

Rejected alternative: arbitrary random walks, polyomino sizes, or extra holes.
Those would widen the area signature, require new exact-axis contracts, and risk
accidental enclosure/merger when packed next to the decoy. They are legitimate
future extensions but unnecessary to demonstrate the reproduced failure. The
small finite shape bank remains a limitation; it is not unlimited shape coverage.

## D4: Remove redundant cage corners
A missing diagonal corner does not break cardinal enclosure, but it creates an
escape path for a wrongly diagonal-connected flood. The original sampler had
no such cases in 600 draws, despite a canonical example that already resolves
the connectivity convention. Compact cages now supply a discriminator in every
slot. Nonrectangular pockets use only the cardinal boundary of the intended
zero region; extra corner walls are unnecessary.

Do not recolor, remove, or reinterpret the actual cardinal boundary. Such a
mutation opens the hole and must change the output. The independent tool tests
60 one-wall breaches per version through the real Racket rule.

## D5: Register counterexamples rather than simply increasing entropy
Add `rectangular_holes_only`, `hole_bounding_boxes`, and `eight_neighbor_holes`
to the rival bank, and link nonrectangular/diagonal witnesses to them. Add the
two canonical-compatible rectangle shortcuts to `CANONICAL_SHORTCUTS`. Expose
`rule_mirror` to the inherited smoke check. All labels still come from Racket;
Python routines are tested mirrors or deliberately incorrect rivals.

The before battery passing all 12 stages proves that a gate's result is only
as strong as the hypotheses it tests. The source-level repair and regression
bank are both necessary: a sampler-only repair could later regress unnoticed.

## D6: Build a reusable independent probe
`workspace/topology_probe.py` uses a border-first zero flood rather than the
generator's region-first helper; compares both to Racket; retains first concrete
rival counterexamples; counts normalized shapes, duplicates, and sliding-window
ambiguity; tests recoloring and a single-wall breach. Its CLI rejects invalid
sampling bounds and returns nonzero for parity errors or missing discriminators
when `--require-witnesses` is requested.

The probe remains under the selected task because this packet forbids shared
edits. Its scope is explicit: reusing it on a task with a different background,
output color, connectivity, or rule would be a false application, not a new
universal quality gate. Canonical shapes, counts, and split lineage cannot be
inferred from coarse dimensions alone.

## D7: Retain negative outcomes and avoid fabricated progress
The eight failing regressions were run before changing the generator. Their
failure logs are retained. The first header-audit hypothesis (silent count
clipping on an undersized board) was rejected by an earlier size error; the
revised finding is unreachable advertised endpoints, not claimed clipping.
`checks/audit-0be8ff9b4144-iteration1.log` retains that failed probe.

The broader repository suite's import failure was reproduced on untouched
framework source rather than hidden, waived as green, or repaired outside scope.
The fresh-solve record is exposure-contaminated by design and says so. No hidden
query scoring or downstream Qwen performance measurement was performed.

## D8: Remaining representational blind spots
Ordinary scenes still have exactly two holes, area at most four, three palette
groups, a finite 9x9 motif arrangement before placement/D4 transformation, and
no default empty-hole branch. Three-hole and wall-island fixtures validate the
independent oracle/reference, **not** sampler support for those cases. Larger
concavities, enclosed islands, variable region counts, and independent object
placement should be separately specified and validated in a later review.
