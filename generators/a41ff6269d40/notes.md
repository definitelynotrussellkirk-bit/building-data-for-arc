# Working notes: a41ff6269d40

## Current rule and authority

The selected canonical Racket rule is unchanged and remains pinned as
`RULE_HASH = "9011a3cbeac9"`.  A connected color-4 source template is normalized
and stamped on a blank output at colored anchor origins: color 1 uses the
identity transform, color 2 reflects left-right, and color 3 reflects up-down.
The source template itself is not copied at its original location unless an
anchor happens to request a copy there.

## Repaired distribution (generator v3.0.0)

The previous v2.1.1 distribution chose anchor colors and polyominoes without
ensuring that a lesson exposed every semantic role.  The retained prior return
`review-a5aa9589b9f6848e:v0001` supplied the decisive lead: easy seed 0,
sample indices 0-2 omitted color 3 from every demonstration, while index 3
introduced color 3 in the query.  The rival “color 3 is identity” therefore fit
all demonstrations and changed the query.  The old distribution also admitted
reflection-symmetric templates, so a present anchor could still fail to reveal
its transform.

The new generator makes the teaching contract constructive:

- every generated input contains colors 1, 2, and 3 among 3-4 anchors;
- each connected 4-7 cell template has pairwise-distinct identity, left-right,
  and up-down forms;
- stamp bounding boxes occupy disjoint quadrants, preventing another stamp from
  hiding the distinguishing pixels;
- a two-step schedule alternates a canonical-size core profile and a broader
  profile across every difficulty band;
- the only advertised controls are real exact controls: `grid_h`, `grid_w`,
  `template_cells`, and `n_anchors`;
- unknown, mistyped, out-of-range, and non-integer controls are rejected;
- `strict_canonical_like`, executable witnesses, declared rivals, and
  `lesson_identifiable` expose the semantic contract to shared checks.

The prior fake/singleton palette, layout, density, and texture axes and the
rule-hiding negative textures were removed from the production domain rather
than relabeled as useful diversity.

## Evidence

Final generator SHA-256:
`062022af105768f36ba1765278dd9792f991b83eff36bf06b77523d368d915dd`.

- Before battery: 3 failed stages and 2 advisory stages; see
  `checks/before/checks/a41ff6269d40_before_battery_summary.json`.
- After battery: 12/12 green; see
  `checks/after/checks/a41ff6269d40_after_battery_summary.json`.
- Focused tests: 40/40 pass; see `checks/task-tests/checks/task_tests.xml`.
- Semantic smoke: 600/600 strict draws, all three witnesses on 600/600,
  12/12 lessons identifiable, and 0/48 ambiguous rotations; see
  `checks/after/checks/a41ff6269d40_after_semantic_gate.json`.
- Large census: 300 lessons, 1,200 pairs, 1,200 query rotations, 1,200 unique
  inputs, and zero ambiguity/warnings/errors; see `checks/lesson-census.json`.
- Exact canonical-shortcut witness and selected-Racket output:
  `checks/question/a41ff6269d40/` and the retained copy under this generator's
  `counterexamples/review-6e327f73fe1ea04f-v0001/`.

## Known limits and open findings

The declared rival set covers the two most direct role-collapse shortcuts
(colors 2 or 3 treated as identity).  Passing those finite rivals is not a proof
of unique induction against every imaginable program.  The production sampler
intentionally covers connected templates of 4-7 cells in 11-18 square/rectangular
grids rather than every lawful grid accepted by the selected rule.  Generated
stamp footprints are deliberately disjoint; overlap/occlusion semantics remain
outside the training distribution.  No Racket authority change was needed.
## Current reviewer considerations

Source SHA-256: `062022af105768f36ba1765278dd9792f991b83eff36bf06b77523d368d915dd`.

# Decisions — a41ff6269d40

Final generator SHA-256: `062022af105768f36ba1765278dd9792f991b83eff36bf06b77523d368d915dd`
Selected rule hash: `9011a3cbeac9` (unchanged)

## D1 — Keep the selected rule; repair only the input curriculum

**Prior choice/rationale.** The selected Racket rule already matched all five
labeled canonical pairs.  No contrary rationale was present in the initially
blank task notes.  The before `rule_smoke`, grammar, Racket lint, and authority
sync stages were green.

**Decision.** Leave the Racket authority unchanged and pin its hash in the
generator.  Repair the generator's sampling and lesson contract instead.

**Alternatives rejected.** Changing the color-to-transform mapping or adding
output behavior would have broken a correct selected authority and hidden the
actual teaching defect.

**Probe/evidence.** `checks/before/...rule_smoke.json`,
`checks/after/...authority_sync.json`, and all five canonical comparisons in
`generators/a41ff6269d40/tests/test_generator.py`.

**Limit.** Authority correctness is established only on the retained canonical
pairs plus generated probes, not by a formal proof of the Racket program.

## D2 — Replace descriptive/fake axes with four exact constructive controls

**Prior choice/rationale.** v2.1.1 advertised palette/layout/density/texture
controls that were singleton, dead, overlapping with negative fixtures, or
silently ignored.  The original rationale is unknown.

**Decision.** Advertise only `grid_h` (11-18), `grid_w` (11-18),
`template_cells` (4-7), and `n_anchors` (3-4).  Validate every request before
sampling, reject unknown keys, and make every legal cross-product constructive.

**Alternatives rejected.** Keeping compatibility aliases would preserve typo
acceptance and unverifiable controls.  Declaring thousands of incompatibility
exceptions would describe implementation accidents rather than a domain.

**Probe/evidence.** Before override gate reported about 9,600 findings, 13,080
legacy multi-axis rejections, two singleton axes, and an accepted unknown key.
The final gate accepted all 17,370 planned draws across 193 cases and three
bands with zero findings: `checks/after/checks/a41ff6269d40_after_override.log`.

**Failure mode/limit.** The narrower advertised API is intentionally breaking
for callers that relied on undocumented ignored keys; such calls now fail
loudly.

## D3 — Use a canonical-size core alternating with broad coverage

**Prior choice/rationale.** The old dimensions mostly missed the canonical
profiles.  Before repair, 0/60 draws exactly matched either canonical profile
and only 1/60 entered the canonical envelope.

**Decision.** Even sample indices use `canonical_core` (12x12, four template
cells, three anchors).  Odd indices draw from the full legal ranges with a
band-specific bias.  The schedule is deterministic and seed-independent so a
short lesson cannot accidentally skip the core profile.

**Alternatives rejected.** Pure rejection sampling was unnecessary and could
make exact overrides flaky.  Using only canonical dimensions would collapse
useful scale diversity.

**Probe/evidence.** Final profile floor is 34/60 exact and 37/60 in-envelope,
with support in every band: `checks/after/checks/a41ff6269d40_after_profile_floor.json`.
The semantic gate observed 308 core and 292 broad draws in 600 samples.

**Failure mode/limit.** This alternation covers both profiles but does not
enumerate every canonical geometry or every schedule start used by an external
assembler.

## D4 — Enumerate connected asymmetric 4-7 cell templates

**Prior choice/rationale.** The old random polyomino sampler did not require the
identity, left-right reflection, and up-down reflection to differ.  As a result,
an anchor could be present yet provide no evidence about its semantic mapping.
The original reason for allowing symmetric shapes is unknown.

**Decision.** Enumerate fixed connected polyominoes deterministically, retain
only shapes with a bounding box at most 4x4 and three pairwise-distinct selected
transforms, then sample from that finite set.

**Alternatives rejected.** Post-hoc rejection from an unbounded random walk
would complicate deterministic replay.  Hand-listing a few shapes would create
a new shape shortcut and weak diversity.

**Probe/evidence.** Focused tests inspect every default draw in 64 indices per
band and assert transform distinctness; semantic witnesses fire on 600/600
shared-gate draws.  The medium-band diversity probe observes at least 40
normalized templates in 160 draws.

**Failure mode/limit.** Rotations other than the two selected reflections are
not separately balanced because they are not rule branches.

## D5 — Put every semantic anchor role in every generated input

**Prior choice/rationale.** v2.1.1 sampled anchor colors independently.  The
retained audit showed three demonstrations with no color-3 anchor followed by a
color-3 query, allowing `color3_is_identity` to fit the lesson.

**Decision.** Start from `[1, 2, 3]`; for a fourth anchor, duplicate one role and
shuffle.  Thus each pair itself refutes both direct identity-collapse rivals
when combined with an asymmetric template.

**Alternatives rejected.** Merely balancing roles over a long corpus does not
make each short lesson identifiable.  Resampling only at lesson assembly would
leave individual generator guarantees implicit and harder to test.

**Probe/evidence.** The retained defect is covered by
`test_lesson_hook_reproduces_and_then_refutes_the_missing_role_defects`.
All-role, horizontal-role, and vertical-role witnesses fire 600/600 in the
semantic gate; the 300-lesson census reports zero ambiguity in production or
under all 1,200 query rotations.

**Failure mode/limit.** This is deliberately redundant teaching.  It gives up
lessons in which a branch must be inferred across examples rather than within
each example.

## D6 — Place stamps constructively in disjoint quadrants

**Prior choice/rationale.** The old layout did not state an occlusion contract.
Even with an asymmetric template, overlap could hide the pixels that distinguish
a transform.  Original rationale is unknown.

**Decision.** Assign each anchor to a different quadrant and sample an origin
whose whole template bounding box fits inside that quadrant.  At most four
anchors are supported, matching the four quadrants.

**Alternatives rejected.** Sequential random placement with retries can fail
valid exact overrides and gives no simple proof of non-overlap.  Allowing
occlusion would require a separate composition-order curriculum and rivals.

**Probe/evidence.** Exact-control tests cover min/mixed/max geometries in every
band, and the 17,370-draw override matrix has no rejection or semantic failure.

**Failure mode/limit.** The repaired generator does not train overlapping stamp
composition.  This is documented rather than silently mixed into the domain.

## D7 — Keep difficulty as a distribution bias, not a rule branch

**Prior choice/rationale.** The old bands changed narrow draw ranges and made
some documented overrides illegal.  Original pedagogical rationale is unknown.

**Decision.** All bands share the same legal cross-product and semantic
contract.  Easy favors smaller grids/templates and three anchors; hard favors
larger grids/templates and four anchors; medium and `None` remain mixed.

**Alternatives rejected.** Band-specific validity ranges were rejected because
an exact control should mean the same thing in every band.

**Probe/evidence.** Every exact override test is parametrized over
`None/easy/medium/hard`; the shared override gate tests the three named bands.

**Failure mode/limit.** “Difficulty” here measures visual scale and multiplicity,
not a proven solver difficulty ordering.

## D8 — Remove production negative textures

**Prior choice/rationale.** The old ordinary texture domain included
`no_template`, `no_anchors`, and `missing_anchor`; some passed weak validation
and some made the rule vacuous.  The original reason for mixing them with
helpful textures is unknown.

**Decision.** Remove the texture axis and all rule-hiding fixtures from the
production generator.  Preserve the prior failure evidence instead of making
negative examples look lawful.

**Alternatives rejected.** `LAWFUL_DEGENERATE_TEXTURES` would be misleading for
inputs that fail to teach the selected branches.

**Probe/evidence.** Before defect lint flagged the overlap, four dead helpful
textures, and the accepted `missing_anchor`; final defect lint is clean.

## D9 — Add a strong validator and observable control extractor

**Prior choice/rationale.** The old `self_check` allowed malformed or
semantically weak instances and did not expose exact control observations.

**Decision.** Validate rectangular integer grids, palette, one connected
color-4 template, anchors, and in-bounds stamp bounding boxes.  Keep
`strict_canonical_like` broad enough to accept all five canonical inputs while
`observe_overrides` gives the framework exact measured values.

**Alternatives rejected.** Requiring all three anchor roles in `self_check`
would reject lawful canonical inputs and conflate the selected rule domain with
the stricter production teaching domain.

**Probe/evidence.** 5/5 canonical inputs accepted; 600/600 generated inputs pass
strict validation.  Focused malformed/palette/disconnected/clipping cases fail.

**Failure mode/limit.** `self_check` validates the selected rule's local safety,
not uniqueness of an inferred rule; semantic witnesses handle the latter.

## D10 — Declare executable rivals and test arbitrary query rotations

**Prior choice/rationale.** No semantic contract existed, so the baseline gate
could only report `NO_CONTRACT` and could not distinguish correct labels from a
teachable lesson.

**Decision.** Declare `color2_is_identity` and `color3_is_identity`, bind them
to horizontal/vertical visibility witnesses, declare the canonical-fitting
color-2 shortcut, and execute `lesson_identifiable` against every demo/query
arrangement.

**Alternatives rejected.** Text-only rival names are not falsifiable.  Checking
only the production query position can hide an ordering-dependent defect.

**Probe/evidence.** Required-rotation semantic gate passes.  The large census
materialized 300 lessons/1,200 unique pairs and tested 1,200 rotations with zero
ambiguous cases, hook warnings, or scoring errors (`checks/lesson-census.json`).
Task-local tests additionally cover all four query positions for 12 cyclic
starts per band.

**Failure mode/limit.** The rival set is finite; no claim of universal program
identifiability is made.

## D11 — Retain an exact canonical-shortcut witness

The strongest canonical-fitting shortcut is “color 2 means identity,” because
the canonical template is left-right symmetric.  The final generator must emit
counterexamples rather than inheriting that bias.  Seed 41, sample index 7, with
12x12 / 6 cells / 3 anchors gives a source-bound exact witness.  The selected
Racket output and shortcut differ at four cells.  Evidence is under
`checks/question/a41ff6269d40/` and copied to the generator's counterexamples.
