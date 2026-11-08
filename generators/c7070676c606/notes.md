# c7070676c606 — current design, version 3.0.4

Selected generator SHA-256:
`e9121bbc33924c5613c73f5c5194251c5a3999be33ee6f23791faccb8366efea`.

## Intended rule and authority

Count color-1 **cells in row 0**. Find same-color four-connected color-3
components; exclude an entire component if any of its cells touches row 0.
Rank eligible components by descending occupied cell count, breaking ties by
their earliest occupied `(row, column)`. Recolor only the component at the
one-based marker rank to color 2. Preserve all other cells.

The selected canonical Racket program remains the label authority, pinned by
`RULE_HASH = "53d5f7ffc079"`; neither it nor its canonical examples changed.
An absent marker, an excessive rank, or no eligible component makes the rank
undefined. A single eligible one-cell component with one marker is lawful.
Diagonal contact is not connectivity. Bounding-box corners do not break ties.
Colors 1, 3 and 2 have fixed roles and are not palette-permutation axes.

## Exact controls and construction

The supported exact integer axes are `grid_h: 10..24`, `grid_w: 11..24`,
`n_shapes: 1..5`, and `k_select: 1..5`. Values must be Python integers, not
Booleans, strings or floating-point coercions. `None` means no override.
Unknown keys, including the former fictitious palette, texture and position
controls, are rejected. A joint request with `k_select > n_shapes` raises a
`ValueError` identifying both axes. A rank-only request constructs enough
components. `observe_overrides` measures these quantities from the pixels.

The general sampler partitions the area below row 0 into chambers separated
by blank rows and columns. Connected shapes grow from sorted frontiers within
their chambers, then receive independent translations. This construction
always supplies the requested component count on the minimum canvas; it needs
no partial-grid fallback. Default general draws use distinct sizes; explicit
override draws retain tied sizes. Both paths may use singletons. Difficulty changes
the general shape-size ceiling (8, 16, 30), while every band receives the same
semantic teaching support. The validator recognizes the broader lawful rule
domain; it does not impose the sampler's minimum dimensions.

## Lesson policy and its limits

The default curriculum assumes **three demonstrations and one query**, drawn
consecutively. Every even sample index emits a varied joint counterexample
to the eight declared canonical-fitting rivals: top-to-bottom order,
bounding-box area/width/height, perimeter, eight-connectivity, total blue-cell
count, and blue-run count. Any four consecutive indices contain two such
inputs, so removing any one as the query leaves a joint witness in the demos.
Rich inputs have four or five eligible green components and descending rank
two. The rich shapes vary by arm length, reflection, padding, profile and
singleton components. Marker placement prevents adjacent rich duplicates.
Two isolated lower blue cells also separate global blue-component count from
top-row cell count: rich inputs have 2 top-row blue cells, 1 top-row blue run,
4 total blue cells and 3 blue components. This refutes the additional natural
solver hypothesis that counts blue components anywhere before ranking green.

Odd indices use varied lawful chamber layouts with distinct sizes, a rank other
than two, and a selection among the bottom two descending size positions:
`n - k + 1 <= 2`. Their selected ascending rank is therefore one or two.
The five fixed descending-rank competitors are refuted twice per four-pair
window: even draws refute constants 1, 3, 4 and 5; odd draws refute constant 2.
The five fixed ascending-rank competitors are also refuted twice: rich inputs
select ascending rank three or four and refute fixed ascending ranks 1 and 2;
odd inputs refute fixed ascending ranks 3, 4 and 5. Every three consecutive
demonstrations show rank variation.

The lesson family contains **26 distinct rivals: 16 canonical-fitting rules
and 10 fixed-rank rules, five in each size orientation**. Nineteen are actively
distinguished by the default schedule: the original eight, the observed global
blue-component rule, and the ten fixed ranks. Seven further canonical-fitting
interpretations remain lesson-only diagnostics: reverse occupied-cell tie order,
bounding-box tie order, dense size ranks, all tied targets, inclusion of top-row
components, clipping top-row components, and all nonbackground objects. These
seven can agree throughout the restricted default support. A passing lesson
means no rival fits its demonstrations and then changes its query; it does not
mean every one of the 26 alternatives was refuted. The canonical and semantic
declarations remain the eight actively witnessed original rules.
Phase 1 modulo 10 supplies
strict canonical support: canonical dimension profiles, input palette
`{0,1,3}`, blue cells confined to row 0, three or four distinct-size components
of at least two cells, and rank three. `LESSON_SCHEDULE_PERIOD = 10`
describes these semantic phases, not a repetition period of complete grids.
The strict hook is a documented manifold check, not an exact shape-template
claim. Explicit overrides select the general sampler and carry no default
lesson-identifiability guarantee.

Default general draws have distinct component sizes, and rich draws have a unique
selected size even when their lower-ranked singleton distractors tie. Therefore
the default curriculum does not ask a solver to infer unseen tie behavior. Ties
remain lawful in the validator and explicit-control generator; exact tie semantics
are verified by retained Racket boundaries. Whole-top-row-component exclusion and
other-color distractors are also boundary support, without a guarantee of teaching
each interpretation in every default lesson.

This is finite-rival evidence, not universal identification. Rich draws have
a recognizable motif and all default rich draws use rank two; generic draws
broaden ranks, sizes and arrangements but do not prove the absence of
conditional or template-based shortcuts.

## Retained evidence and replay tools

`tests/test_review_contract.py` tests exact axes, rejection policy, canonical
shortcut fit, determinism and all-query-position witness support.
`tests/test_rank_teaching.py` checks the retained constant-rank ambiguity and
rank variation throughout the declared schedule. `tests/test_tie_teaching.py`
retains an actual ambiguous Racket-labeled lesson, checks the seven added rivals,
default size uniqueness, and lawful override ties. Rotation regressions require
each rival either to agree on every pair or to have at least two refuting pairs,
so holding out one refuter cannot leave a different query answer unsupported.
`tests/test_semantic_boundaries.py` uses an independent union-find oracle and
canonical helpers. `counterexamples/semantic_boundaries.json` retains five
lawful cases with exact outputs and four invalid-rank cases, bound to the
selected rule. `workspace/check_semantics.py` replays them through one Racket
bridge, records source/runtime hashes and fails if source bytes change.
It does not supply labels from a Python generator mirror.
`tests/test_blue_component_teaching.py` checks the observed blue-component
hypothesis, marker-count contrasts and its actual Racket-labeled before lesson.
`tests/test_ascending_rank_teaching.py` freezes the second-smallest ambiguity
and checks both fixed-rank orientations across all ten start residues, three
seeds and every difficulty band.
`counterexamples/teaching_failures.json` retains the four minimal actual lesson
failures with source/report hashes, addresses and original Racket labels;
`tests/test_retained_teaching_failures.py` loads these files through the portable
root helper and verifies that their ambiguities remain detectable.
`workspace/review_resources.py` estimates runtime and portable-test staging
space from a retained manifest and optional packet ZIP, without copying or
deleting files; use it before scheduling concurrent review commands.
`workspace/check_lesson_contrasts.py` flags task-designated observable values
that are constant in demonstrations but change in the query. It is an input-only
diagnostic for proposing rivals, not a substitute for Racket labels or a rule
that all query values must appear in demonstrations.

The original notes contained no design rationale. Version 3 replaces ignored
controls, rank clamping, dead texture declarations, a weak cell-count validator
and retry-based placement. The review's before/after logs and red regressions
retain that evidence; current decisions are documented here without copying
the full review history. Version 3.0.1 also reverses the initial independent
odd-rank choice: the exposed solve revealed constant-rank ambiguity, and replay
of the first 300-lesson census found 28 production and 127 rotation failures
against constant rank two. Forcing odd default ranks away from two supplies
the missing contrast; the original solve and counterexamples remain retained.
Version 3.0.2 reverses the choice to allow size ties in default odd draws. Rescoring
the 3.0.1 census against the seven additional interpretations found 20/300 production
and 73/1,200 rotation ambiguities from reverse ties, all tied targets and dense ranks.
Default distinct sizes remove that unsupported query distinction while retaining
the broader lawful domain and explicit-control support. Both earlier exposed solves,
the exact failing lessons and their original source snapshots remain in the review.
The next fresh solve then exposed a specific composition of the blue-count
alternatives: global blue-component count. It fit the 3.0.2 episode's visible
demonstrations, and independent replay found 31/300 production and 122/1,200
rotation ambiguities. Version 3.0.3 therefore adds the second separate lower
blue cell to every rich witness and declares the exact observed rival. The
prior single distractor had accidentally made blue-component count equal the
intended rank. Generic contiguous marker groups remain supported; changing
all markers to isolated cells would have hidden that distinction instead.
The version-3.0.3 worker then identified the intended rule but noted that
second-smallest selection fit its visible examples. Independent replay of the
public 3.0.3 census found a union of 10/300 production and 41/1,200 rotation
ambiguities across fixed ascending ranks 1..5. Version 3.0.4 increases rich
candidate count to four or five and restricts odd default selections to the
bottom two size positions while excluding descending rank two. This closes the
measured finite rank-family contrast without restricting lawful overrides.
The source-bound report and exact Racket-labeled before lessons are retained
under the review's `checks/ascending-ranks/` and `checks/ascending-rank-teaching/`.

All four prior exposed episodes and their honest assumptions remain retained.
The v3.0.4 implementation run passed 492 focused tests before the fourth retained
teaching-failure case was added; all four retained cases then passed separately.
The final battery passed all 12 stages. The source-bound census materialized 300
three-demonstration/one-query lessons and 1,200 required holdout rotations with
zero declared-family ambiguity, using 1,069 distinct inputs. Fixed seed 0 covered
all ten starts in each band: 30 lessons, 120 rotations, 23 distinct inputs and
zero ambiguity. Detailed counts, the final portable suite and exact-patch replay
receipts are reported in the return's REVIEW.md and RESULTS.json. Untested rival
families and the distribution restrictions above remain explicit limitations;
passing review checks does not change training approval.
## Current reviewer considerations

Source SHA-256: `e9121bbc33924c5613c73f5c5194251c5a3999be33ee6f23791faccb8366efea`.

# Decisions — c7070676c606

Final generator: **3.0.4**, SHA-256
`e9121bbc33924c5613c73f5c5194251c5a3999be33ee6f23791faccb8366efea`.
Assignment `review-35316dedd6e945e7` and both audit targets remain unchanged.
The original notes were a placeholder; the original author's rationale is
unknown. The decisions below distinguish the baseline's observed behavior,
the repair, evidence, and remaining limits.

## D1 / R1 — validate the selected rule's domain

The reference counts blue **cells in row 0**, then ranks same-color,
four-connected green components that lie entirely below row 0. Descending
occupied cell count determines rank; the earliest occupied `(row, column)`
breaks equal-size ties. A component touching row 0 is excluded in its entirety.
Other input cells are preserved. Colors 1, 3 and 2 are fixed semantic roles.

The old validator counted green cells below the first row. It rejected a
lawful singleton, accepted two markers with only one eligible two-cell shape,
and accepted a component whose below-row cells all belonged to a component
touching row 0. Those are distinct failures of eligibility and rank validity,
not merely shape-style preferences. The new validator checks rectangular
integer ARC grids and exactly `1 <= k <= eligible_component_count`.

We rejected a minimum-two-components rule, clipping row 0 off crossing
components, eight-connectivity, and bounding-box tie order. Their disagreement
with the selected rule is retained in
`repo/generators/c7070676c606/counterexamples/semantic_boundaries.json` and the
Racket replay reports. The boundary tests use an independent union-find oracle;
production code uses the shared component helper. The Python diagnostic
prediction is not the label authority.

The five lawful and four invalid fixtures cover singleton endpoints, row-1
eligibility, whole-component exclusion, occupied-cell ties and a joint rival
witness. The replay checker requires the pinned rule's missing-target error
signature on invalid ranks; an unrelated missing-rule or bridge error fails.

## D2 / R2 — make controls exact and observable

| Control | Supported domain | Reason and implementation |
|---|---|---|
| `grid_h` | Integer 10–24 | Covers all canonical heights and broader lawful canvases; honored exactly. |
| `grid_w` | Integer 11–24 | Covers all canonical widths, including the 10×11 minimum profile. |
| `n_shapes` | Integer 1–5 | Counts eligible green components from pixels; includes the lawful one-object endpoint. |
| `k_select` | Integer 1–5 | Exact row-0 blue-cell count; rank-only requests construct enough components. |

The baseline ignored several controls and clamped rank. Silent coercion and
clamping hide a caller's requested population, so the new API rejects Boolean,
floating-point and string values, out-of-range values, unknown controls and
explicit `k_select > n_shapes`. The last error identifies both incompatible
axes. `None` means no override. The old palette, position and texture controls
were untruthful or degenerate; they are removed rather than retained as inert
aliases. There is no color permutation axis because the Racket rule assigns
literal colors their roles.

The validator accepts a broader lawful domain than the sampler. In particular,
the compact 10×10 explanatory witness is legal but outside the advertised
minimum generated width. The question answer separately supplies a real
13×13 final-source generated witness and its exact seed/index. This distinction prevents
conflating a useful counterexample with measured generator support.

## D3 / R2 — construct complete layouts without retries

The previous placement loop could return an incomplete grid. The new general
sampler partitions the area below row 0 into rectangular chambers with a
blank row or column between them. It grows a connected polyomino in each
selected chamber using a sorted frontier, then translates it within that
chamber. Every supported minimum-size layout has positive chamber capacity,
and a connected rectangular chamber always has a frontier until it is full.
There is no rejection loop or partial-grid fallback.

We rejected merely increasing retry limits: that would lower a failure rate
without establishing exact count support. Difficulty sets general shape-size
ceilings of 8, 16 and 30 cells, while chamber arrangement, translations and
growth vary. Ties and singletons are lawful; default general draws use distinct
sizes, while explicit controls retain ties (D8 explains this restriction).
Sorting the growth frontier makes
seeded choices independent of set-iteration order.

Chambers restrict support: they do not cover every arrangement of interleaved
or touching bounding boxes. This is an explicit construction tradeoff, not a
claim to sample all lawful ARC grids. Hand-authored boundary fixtures exercise
important semantics beyond that layout family.

## D4 / R3 — teach rivals with repeated contrasts

The strongest simple canonical-fitting rival is “choose the kth green object
from top to bottom.” Bounding-box area, width, height, perimeter,
eight-connectivity, global blue-cell count and top-row blue-run count also fit
every usable canonical pair. A compact joint witness has a small L, a
diagonally adjacent domino, a lower solid rectangle, adjacent top-row markers
and a lower blue distractor. The true rank and all eight rival predictions
separate on this one input. Exact grids and actual Racket outputs are in
`QUESTION_ANSWER.md` and its linked evidence.

Every **even** default index generates a varied member of this rich family.
Its L arm, reflection, padding, canonical-size profile and extra singleton
components vary. Every **odd** index generates a general lawful layout.
Four consecutive inputs contain two rich witnesses; holding out any one pair
still leaves at least one in the demonstrations. A single rich witness per
lesson was rejected because moving it to the query would remove the teaching
contrast. Marker starts and the presence/absence of lower blue cells prevent
within-window duplicates from silently changing the accepted-index schedule.

## D5 / R3 — repair a genuine weakness found by the solve

The first repaired version independently drew odd ranks. The exposed solve
then received three demonstrations with rank two. Its visible-only work log
correctly noted that a constant-rank-two rule also fit those demonstrations.
This was a genuine successful solver attempt with an explicit assumption, not
an invented failed solution. Its complete record remains under
`checks/prior-solve/v3.0.0/`.

An independent replay of the authorized, Racket-labeled 300-lesson census
confirmed **28/300 production ambiguities and 127/1,200 rotation ambiguities**
against constant rank two. The earlier eight-rival census had found none
because this rival does not fit all canonical pairs and had not been declared
as a lesson competitor. Exact production and rotation cases, counts and
reproduction scripts are in `checks/rank-teaching/`.

Version 3.0.1 therefore forces every odd default rank away from two and makes
phase-1 strict anchors rank three. Even rich inputs remain rank two. The five
constant-rank alternatives are declared only in `LESSON_COMPETITORS`, giving
**13 distinct lesson rivals at that version**; the eight actively witnessed
canonical-fitting rivals remain in their canonical and semantic declarations.
Version 3.0.2 extends the lesson-only family to 20 as described in D8, and the
natural solver hypothesis in D9 brings version 3.0.3 to 21. The five fixed
ascending ranks in D10 bring version 3.0.4 to 26. Repeated reporting namespaces do not represent additional distinct rules.

Each four-pair window now has two refutations of constant rank two (the odd
pairs) and two of constant ranks 1, 3, 4 and 5 (the even pairs). Any three
consecutive demonstrations show rank variation. Exact overrides deliberately
use the unrestricted general sampler, including explicit rank two; they carry
no promise about the default lesson curriculum.

## D6 — canonical support and schedule scope

The declared period is **10**, combining the parity teaching schedule and the
phase-1 canonical anchors. It is a period of semantic phases, not a claim that
random grids repeat every ten indices. Strict anchors use exact canonical
dimension profiles, palette `{0,1,3}`, blue only in row 0, three or four
components with distinct sizes of at least two, and rank three. The strict
hook accepts both canonical ranks two and three and all three canonical
inputs; it describes a manifold, not a list of memorized shape templates.

Production evidence uses three demonstrations plus one query in consecutive
sampler order. Required rotations hold out each of the four materialized pairs
once and preserve the remaining order. The fixed-seed census enumerates all
ten start residues in every band at seed 0. The wider census uses 100 lesson
indices per band, with seeds derived by the public census recipe. Complete
reports retain actual seeds, accepted indices, labels and input hashes.
Overlapping windows and cross-band duplicates are counted explicitly; lesson
counts are never presented as unique-input counts.

These checks establish finite declared-rival support. The rich family remains
recognizable, with a below-row blue cue associated with rank two. A conditional
program could exploit that association. Other imaginable variants are not
silently covered by twenty-six named rivals. Alternative tie, top-row and color-filter
interpretations now have explicit lesson diagnostics but can agree on all default
inputs; their distinguishing boundaries are separately tested. Arbitrary conditional
rivals remain unexhausted. No training-approval or
admission setting changed.

## D7 — retain useful tools, failures and independent evidence

The task-owned `workspace/check_semantics.py` replays frozen boundaries through
one Racket bridge, recording source, rule, fixture, checker and runtime hashes.
It avoids another copied runtime while keeping Python mirrors out of expected
labels. `workspace/review_resources.py` estimates staging space from a real
manifest and optional ZIP. The contrast diagnostic described in
`FEEDBACK_TO_CODEX.md` checks observable selector variation before stronger
semantic claims are made. These are reusable, reviewable code artifacts.

The first battery's missing rule pin, weak controls, dead metadata, profile
warnings and absent semantic contract remain retained. So do the lexical lint
warning in the intermediate version, red regression runs, the exposed solve
that found constant-rank ambiguity, and the portable test staging ENOSPC
failure. Resource failures are not counted as generator assertion failures.
The root coordinator's initial asynchronous-copy race is documented as an
orchestration error, not attributed to the packet.

Only the selected task's files change. The two audits are separately reported
in `AUDIT.md`, with exact source-bound reproductions and untouched target
sources. The final handoff replays the exact generated delta in a fresh
extraction, verifies its generator identity, reruns all focused tests there,
and binds the final exposed solve to the same source bytes.

## D8 / R4 — keep unsupported tie distinctions out of default queries

A bounded check of seven further canonical-fitting interpretations found a
second concrete teaching defect in version 3.0.1. On its retained, public,
Racket-labeled census, reverse tie order, recoloring all tied targets and dense
size ranks produced a union of **20/300 production ambiguities and 73/1,200
rotation ambiguities**. The exact first lesson has seed `1753406524`, band
`easy`, start index `0`, and query sample index `3`: one top-row marker and
eligible sizes `[7,7,7,1]`. Reverse tie order and all tied targets fit all three
demonstrations and change that query. `checks/additional-rivals/` retains the
independent scorer, counts and exact Racket-backed counterexamples.

Version 3.0.2 makes all default odd sizes distinct. Phase-1 anchors still use
sizes of at least two; other general defaults may include a singleton. Chamber
capacity supplies at least as many available sizes as components on the minimum
canvas, so this choice preserves constructive completion. Rich even examples
already have a unique selected rank despite possible ties among lower singleton
distractors. Explicit non-None overrides keep the unrestricted general path,
including ties. The validator continues recognizing lawful tied inputs.

We chose this distribution restriction because canonical examples do not teach
tie handling, and the intended default lesson contract should not require that
unsupported distinction in a query. Rejecting ties in the domain validator would
misrepresent the Racket rule; adding a new family of tie lessons would introduce
another schedule and teaching obligation. The retained boundary fixtures and
explicit-control sampler remain the place to exercise the broader tie semantics.
Consequently this curriculum does not claim to teach the entire lawful domain.

All seven additional interpretations are pure `LESSON_COMPETITORS` mirrors,
bringing that family to **20 distinct rules**: 15 fit all canonical pairs and
five are constant ranks. The original eight actively separated rivals remain
`CANONICAL_SHORTCUTS` and `SEMANTIC_RIVALS`; the seven additions are allowed to
agree across the default support. The rotation invariant is therefore zero or
at least two refuting pairs per four-pair window. Zero refutations is harmless
for these inputs because the held-out prediction also agrees; one refutation
would create an unsupported query when that pair is held out. Reports claim
zero differing-query ambiguities, never that every rival was refuted.

The new 99 regressions first yielded 25 failures on the frozen 3.0.1 source;
the repaired suite contains 295 passing focused tests. Both earlier successful
visible solve episodes remain intact with their original assumptions. The 3.0.1
solver's all-tied extrapolation is useful evidence of what those demonstrations
did not establish, not an intentionally fabricated wrong solution. This bounded check completed the planned tie/eligibility family. Subsequent
fresh solver episodes produced the concrete hypotheses in D9 and D10; they
were investigated because they were observed, not as an open-ended search. Arbitrary conditional hypotheses remain
an explicit finite-testing limit.

## D9 / R5 — separate blue cells from blue connected components

The fresh version-3.0.2 worker independently chose this rule: count all blue
four-connected components, then select that descending size rank among all
green four-connected components. Its sole official attempt matched all three
visible examples; masked correctness remained unknown. The work log is retained
unchanged under `checks/prior-solve/v3.0.2/`. We did not supply the intended rule
to the worker or revise its program after seeing its hypothesis.

The rich template's adjacent pair of top-row blue cells formed one component,
and its single lower blue cell formed another. That accidentally made this
alternative count equal two. General odd inputs can contain adjacent top-row
markers without lower blue, so the coincidence did not hold throughout default
support. An independent union-find implementation matched the archived public
solver on all 1,106 unique inputs in the authorized 3.0.2 census. It found
**31/300 production ambiguities and 122/1,200 rotation ambiguities**, and the
alternative also fit all three canonical pairs. Exact Racket-labeled instances,
counts and executable reproduction are in `checks/blue-components/`.

Version 3.0.3 adds one more isolated blue singleton, two columns from the old
one on the same lower row, with the same reflection. Both lie below all green
shapes. Each rich input now has top-row blue-cell count **2**, top-row blue-run
count **1**, global blue-cell count **4**, and global blue-component count **3**.
The new rival selects green rank three while the selected rule chooses rank
two. The original eight rival contrasts and the seven agreeing interpretations
remain intact. Two rich pairs in every four-pair window preserve this contrast
under every single-pair holdout.

We rejected isolating every generic marker: that would remove lawful adjacent
marker support and allow the blue-component interpretation to keep agreeing
by construction. The second distractor preserves the broader marker layout
support and provides the missing distinction. All four exact axes, candidate
packing and strict canonical anchors remain unchanged.

The exact observed hypothesis is a pure lesson-only mirror, including its
choice to rank green components touching row zero. That additional convention
does not change its fit on the canonical or default inputs, which have no
top-row green. At version 3.0.3 the family was **21 distinct rivals: 16 canonical-fitting
alternatives and five constants; 14 were actively refuted, seven agreed on the
restricted default support**. The eight original canonical/semantic declarations
remain an actively witnessed subset, not an exhaustive list of plausible rules.

The 92 new tests first failed on the frozen 3.0.2 source and then joined a
387-pass focused suite. Three additional portable data regressions retain the
actual constant-rank, tie and blue-component failures together in the task's
`counterexamples/teaching_failures.json`; that version's suite contained 390 cases.
These stored labels are copied from the public Racket censuses, not generated by
a Python prediction. Actual source-bound before lessons remain ambiguous and
are correctly reported by the diagnostic hook; new default lessons supply the
missing contrasts. D10 records the subsequent observed rank-orientation defect.

## D10 / R6 — distinguish both fixed size-rank orientations

The fresh version-3.0.3 worker inferred the intended marker-indexed descending
rule but explicitly noted that selecting the second-smallest component also fit
all visible examples. Its unchanged public episode and assumptions are retained
under `checks/prior-solve/v3.0.3/`. Together with the preceding three episodes,
there are four prior exposed solve records; none is recast as a blind attempt.

Independent replay of the authorized public Racket-labeled 3.0.3 census against
fixed ascending ranks 1..5 found a union of **10/300 production ambiguities and
41/1,200 rotation ambiguities**. Second-smallest alone accounted for 8 production
and 30 rotation ambiguities; ascending rank three accounted for 1/7 and rank
four for 1/4. The first saved second-smallest production lesson is medium seed
`2940377972`, requested start `11`, query sample `14`. Its query has two top-row
blue cells and ascending eligible green sizes `[1,2,4,6]`: the selected Racket
rule recolors the size-four component, while second-smallest selects size two.
The alternative fits all three actual demonstration labels. The independent
scorer, full five-rank findings and exact before cases are in
`checks/ascending-ranks/`; an unchanged report copy, frozen regression lesson,
red/green logs and source-bound receipt are in `checks/ascending-rank-teaching/`.

Version **3.0.4** makes every rich default input have four or five candidates
with descending rank two, hence ascending rank three or four. Every odd default
input retains distinct sizes, excludes descending rank two, and satisfies
`n - k + 1 <= 2`, selecting one of its two smallest sizes. Phase-1 strict anchors
remain rank three with three or four distinct components of at least two cells.
Exact non-None overrides retain the unrestricted general sampler, including
`n_shapes=3, k_select=2`, all legal ranks and lawful ties. The validator continues
to accept the broader selected-rule domain. The two lower blue singleton
contrasts and the original eight witnesses remain in place.

Each four consecutive default pairs has two rich inputs and two odd inputs.
Both rich inputs refute fixed ascending ranks 1 and 2; both odd inputs refute
fixed ascending ranks 3, 4 and 5. Both rich inputs also refute fixed descending
ranks 1, 3, 4 and 5, while both odd inputs refute fixed descending rank 2.
Therefore every fixed rank in either orientation has at least two refuting
pairs, leaving one among the demonstrations under any single-pair holdout.
This closes the observed finite rank family, not arbitrary conditional programs.

The final family contains **26 distinct lesson competitors: 16 canonical-fitting
rules and 10 fixed ranks**. Nineteen are actively distinguished by the default
schedule: eight original rules, global blue-component count and ten fixed ranks.
The seven tie/eligibility interpretations may agree throughout default support;
the invariant remains zero or at least two differing pairs per four-pair window.
`CANONICAL_SHORTCUTS` and `SEMANTIC_RIVALS` remain the original eight actively
witnessed rules. The report does not claim that all 26 competitors are refuted.

The 102 new regressions first produced 78 failures and 24 passes on frozen
3.0.3 source `9269425171b2ef8fe5b11d4e14006d54cf2cdd2f0a5ee7d4e20d8ce8ab533d4e`.
After repair the implementation's focused suite passed **492 tests**, including
independent BFS checks of both rank orientations over all ten start residues,
three seeds and all three difficulty bands. The retained teaching-failure JSON
now contains four source-bound cases. The exact delta then applied to a fresh
original extraction, where the public portable stage passed **493/493 cases**,
with zero failures, errors or skips (`checks/fresh-replay/report.json`).
The selected final source is
`e9121bbc33924c5613c73f5c5194251c5a3999be33ee6f23791faccb8366efea`.
The v3.0.4 battery passed all 12 stages. The final 300-lesson census found zero
production and zero ambiguity across 1,200 required rotations, with 1,069 unique
inputs (easy 381, medium 382, hard 380, with overlap across bands). Fixed seed 0
covered all ten starts in every band: 30 lessons, 120 rotations, 23 unique inputs,
and no ambiguity. All 19 actively distinguished competitors were refuted in every
production lesson; the other seven agreed on all pairs. These are finite-family
results, not a proof against untested programs. Compared with v3.0.3's 1,108 unique
inputs, the narrower final rank schedule produced 39 fewer unique inputs in the
same census. Fresh exact-patch handoff results are recorded in REVIEW.md and
RESULTS.json. No training approval or admission setting changed.
