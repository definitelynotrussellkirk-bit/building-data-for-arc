# Current notes: 7c2b3290ba62

## Intended rule

Split the input at full-height color-9 columns into equal panels:
`SOURCE | TARGET | CANDIDATE_0 | ...`. Treat every nonzero, non-9 cell as
occupied, independent of its color. Find the unique unordered candidate pair
whose occupied-coordinate union with `SOURCE` equals `TARGET`. Return a `1 × N`
row with cyan 8 at those two candidate indices and 0 elsewhere.

The selected canonical authority is pinned by `RULE_HASH = "8518d3e47ce6"`.
Version 3.1.0 does not modify the Racket rule.

## Current construction

The generator constructs, rather than searches for, one lawful answer pair:

- `SOURCE` is a nonempty proper subset of `TARGET`.
- `TARGET - SOURCE` is partitioned into two nonempty, disjoint candidate panels.
- Every distractor avoids `SOURCE` cells and includes at least one cell outside
  `TARGET`, so no pair involving a distractor can complete the target.
- Cyan 8 is reserved for the output marker and never appears in the input.
- Candidate panels are monochrome with distinct colors. In the seven-candidate
  lane, the seven available input occupancy colors 1..7 force exactly one
  candidate to reuse the `SOURCE`/`TARGET` color; color identity is not part of
  the rule.

Three exact controls are supported: `panel_h` in 3..6, `panel_w` in 2..4, and
`n_cands` in 3..7. Width-incompatible combinations are declared and rejected
rather than silently clamped. `observe_overrides` reports all three realized
values.

## Curriculum and canonical support

`sample_index mod 4` selects one of four profiles. Profile 0 is an exact
canonical-shape/palette lane: 4 rows, six 4-column panels, total width 29,
seven input colors, four singleton candidates, and a one- or two-cell source.
It occurs in every difficulty band. Other profiles widen geometry and candidate
count.

The output alphabet is finite: for candidate counts 3..7 there are
`C(3,2)+...+C(7,2)=55` legal marker rows. The unbanded default schedule and the
answer-pair schedule cover all 55 within the generic linter's 24-episode,
six-example horizon. This is declared as `EXPECTED_OUTPUT_CODOMAIN = 55`.

## Teaching contract

Every normal draw refutes these declared rivals:

1. Ignore `SOURCE` and union only the two candidates.
2. Intersect, rather than union, the two candidates.
3. Select a single candidate that completes the target.

`SEMANTIC_WITNESSES` checks the corresponding source-required,
disjoint-complement, and pair-required properties. `lesson_identifiable`
requires every declared rival to be contradicted by the demonstrations and to
predict the labeled query correctly. `EXAMPLES_NEEDED = 2`.

## Reversed prior choices

The 2.3.0 source exposed many advertised texture controls that did not change a
normal draw, mixed negative fixtures into the ordinary texture domain, silently
clamped candidate count to fit width, used one shared occupancy color, and had
no canonical rule hash or task-local tests. Those choices were removed rather
than patched around. Their stated rationale is otherwise unknown; no historical
return was used as evidence beyond the pinned assignment and current source.

An intermediate 3.0.0 version widened to seven candidates by allowing color 8
inside panels. Defect lint correctly reported transformation drift because the
canonical output marker was no longer introduced. Version 3.1.0 reserves 8 for
outputs and reuses the source color once only in the seven-candidate lane.

## Final evidence

Final generator SHA-256:
`220eeadbb6ff92aa8a3e0060360b410d5e2bf668e07e6d3383472ccd9028f91b`.

- After battery: 12/12 stages green, no advisory or failed stage.
- Focused portable task tests: 40/40 passed.
- Semantic gate: 600/600 generated inputs satisfy all three witnesses;
  12/12 smoke lessons identifiable; diagnostic rotations 0/36 ambiguous.
- Larger census: 300/300 lessons materialized, 900 unique inputs,
  0/300 production ambiguities, and 0/900 rotated-query ambiguities.
- Profile floor: 20/60 exact canonical-profile draws, with at least one in every
  band.
- Override matrix: 5,580 draws, 5,040 accepted, 540 declared incompatible
  rejections, zero findings.
- Lint: 55 distinct outputs over 144 pairs and complete declared codomain
  coverage.

Evidence is retained under `WORK/checks/after-v4/`,
`WORK/checks/task-tests-v4/`, and `WORK/checks/lesson-census-v4.json`.

## Known limits

- The finite rival set is not a proof of unique induction against every possible
  program.
- The canonical-profile lane matches public shape, palette cardinality, and
  object-count family, not the exact public grids.
- The production sampler's ordered two-demo lessons and all query rotations were
  tested, but not every conceivable custom lesson assembly.
- Training approval remains outside this review; passing checks do not mark the
  generator approved or train-safe.
## Current reviewer considerations

Source SHA-256: `220eeadbb6ff92aa8a3e0060360b410d5e2bf668e07e6d3383472ccd9028f91b`.

# Decisions: 7c2b3290ba62

## D1 — Keep the selected Racket rule unchanged

**Choice.** Treat occupancy as every value except 0 and separator 9; find the
first/unique candidate pair whose union with `SOURCE` equals `TARGET`; output a
1×N row with two 8s.

**Basis.** All canonical pairs agree, and the selected rule hash is
`8518d3e47ce6`. Rule smoke and authority sync pass on the final source.

**Alternative rejected.** Patch the Racket rule to enforce uniqueness or color
roles. Canonical evidence did not justify changing authority; uniqueness is a
generator-domain invariant instead.

**Limit.** The rule itself returns the first matching pair on an ambiguous
input. The generator and self-check exclude ambiguity.

## D2 — Remove fake texture controls; expose only exact observable geometry

**Choice.** Support `panel_h`, `panel_w`, and `n_cands` as strict integer axes.
Reject unknown keys, bool/float/string coercions, out-of-range values, and
width-incompatible linked combinations. Report realized values through
`observe_overrides`.

**Prior choice.** Version 2.3.0 advertised helpful and degenerate textures,
although normal helpful textures were byte-identical and negative fixtures
shared the ordinary valid domain. Candidate count was silently reduced to fit
width. The original rationale is unknown.

**Alternatives considered.** Make the texture values real; or retain them as
diagnostic fixtures. Both add vocabulary without improving the task concept.
Exact geometry axes are smaller and falsifiable.

**Evidence/failure mode.** Baseline override checks produced hundreds of
findings. Final override check exercised 5,580 calls with zero findings and 540
structured incompatibility rejections.

## D3 — Construct one unique semantic answer, not merely a Racket-valid input

**Choice.** Make `SOURCE` nonempty and a proper subset of `TARGET`; partition
all missing target cells into two nonempty disjoint candidates; give every
distractor an outside-target cell and no source cell.

**Why.** This proves one completing pair and forces the source and both
candidates to matter. It also makes common wrong rules mechanically testable.

**Alternatives rejected.** Randomly sample panels until the rule happens to
fire; or allow source-empty/single-candidate completions as ordinary data. Those
weaken the lesson and can admit shortcut labels.

**Limit.** The construction covers a disciplined task domain, not every lawful
ambiguous or adversarial input the Racket rule could receive.

## D4 — Add an exact canonical-profile lane in every band

**Choice.** Every fourth sample uses 4 rows, panel width 4, four candidates,
width 29, seven input colors, singleton candidates, and canonical source/target
occupancy counts.

**Why.** The baseline generated exactly three colors while canonical median was
seven. A scheduled lane gives measurable support without exact replay.

**Alternative rejected.** Rely on random chance to hit public shape/palette.
The profile-floor probe showed that chance was insufficient.

**Limit.** Structural profile equality does not imply exact public-distribution
matching.

## D5 — Reserve cyan 8 for output and vary input panel colors

**Choice.** Inputs use occupancy colors 1..7 only. Candidates are distinct in
color; with seven candidates, exactly one necessarily shares the source color.

**Intermediate reversal.** Version 3.0.0 used colors 1..8 to keep source and all
seven candidate colors distinct. Defect lint then found transformation drift:
8 was already present in most inputs even though canonical examples always
introduce it. Version 3.1.0 reserves 8 for output.

**Alternative considered.** Drop the seven-candidate lane. That would avoid the
palette constraint but reduce useful finite label coverage. Because color is
provably ignored, one source/candidate color reuse is the narrower compromise.

## D6 — Cover the complete finite output alphabet deliberately

**Choice.** Candidate counts span 3..7 and answer pairs use a deterministic
low-discrepancy schedule. Declare the exact codomain size 55.

**Why.** Pure random pair placement left the generic lint horizon below its
diversity threshold. The rule's output is intrinsically finite; the correct
response is complete support, not arbitrary noise.

**Alternatives considered.** Keep counts 3..6 and declare the 34-label codomain;
or suppress the warning. The 3..7 lane fits ARC width, tests more indices, and
covers all 55 labels. Suppression was rejected.

**Evidence.** The exact linter horizon now observes all 55 labels in 144 pairs.

## D7 — Require executable teaching witnesses and lesson-level rival checks

**Choice.** Declare rivals for ignoring source, intersecting candidates, and
using one candidate. Require source contribution, disjoint complements, and the
need for a pair on every input. Two demonstrations must refute every rival and
support the query.

**Why.** Correct per-grid labels do not guarantee that a lesson teaches the
intended rule.

**Alternatives rejected.** Narrative-only notes or per-input self-check alone.
Neither detects a rival that fits all demonstrations but differs on the query.

**Evidence.** Semantic gate: 600/600 witness activations and 12/12 identifiable
smoke lessons. Larger census: 300/300 lessons and all 900 query rotations with
zero declared-rival ambiguity.

**Limit.** This is finite rival testing, not a universal induction proof.

## D8 — Add a task-local portable regression suite

**Choice.** Add 40 tests covering canonical parity, exact controls in all bands,
invalid calls, determinism/freshness/global RNG purity, source/rival witnesses,
canonical scheduling, all cyclic lesson starts, full finite codomain coverage,
and destructive mutations.

**Why.** The baseline had no task-local tests and its broad self-check did not
encode these contracts.

**Evidence.** Portable `task_tests` stage passes 40/40. Test file SHA-256:
`130daadd76e18938e636e62ffbb51dc46378ff1e1dc4e8ef7305ae25a0ca6fbe`.

## D9 — Add a native completing-pair → selected-size-role family

**Choice.** Keep production `generator.py` and canonical authority unchanged.
Add task-local `marker_mode={pair_cyan,size_roles}`. `pair_cyan` executes the
canonical Racket program byte-for-byte. `size_roles` first finds the unique
candidate pair that completes TARGET with SOURCE, then colors the larger
selected candidate cyan 8 and the smaller selected candidate red 2.

**Sequential dependency.** Step A returns the completing pair. The intermediate
is that pair together with the occupied-cell counts of its two members. Step B
assigns the two role colors only inside the selected pair. Global candidate size
is not a substitute: every lesson contains an unselected distractor larger than
at least one selected part, and the two minimum demonstrations reverse which
selected index is larger.

**Evidence.** The native adapter supports 2–6 demonstrations and exactly four
prefix-stable queries, including a substantive 30x29 boundary case (equal-width
panels plus one-column separators cannot total exactly 30 columns here). A
finite nine-rival teaching audit covered both settings, seeds 0/17/31, and
2/3/6 demonstrations; selected labels and the declared setting rival were
executed through protected Racket. Native qualification passed both settings at
seeds 0 and 17 with three demonstrations and four queries. The protected
counterfactual reverses the selected size-role intermediate and changes both
nonzero output cells on a qualified 30x29 query.

**Limit / next action.** Finite rivals are not a universal identifiability proof.
This return is reviewer-ready only: the owner must integrate these exact source
bytes, rerun native qualification and the protected witness, perform fresh
acceptance on the live tree, and separately decide any training admission.
