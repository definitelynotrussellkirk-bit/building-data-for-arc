# Parallel Bars Become Solid — current generator notes

## Authority and domain

Version 2.0.0 pins unchanged canonical `RULE_HASH = 220859949b76`.
Extract same-color **four-connected** components once from the input. A bar is a
contiguous one-column component of height at least two. Group bars by exact
`(color, top row, bottom row)`, sort columns, and fill disjoint adjacent pairs
from the left. A trailing odd bar stays unpaired. A different row span forms a
different group, even when height and color match. Input components are not
recomputed after painting.

The generator deliberately uses a bar-only subset: background zero, legal
integer colors, at least one fillable pair, no overlapping pair rectangles,
and no overwrite of a different color. An unmatched same-color bar may lie
inside a pair rectangle and protrude outside it; this teaches exact span
matching and static extraction. Canonical inputs are accepted. The Racket
rule also handles ignored nonbar components and order-sensitive conflicting
fills; those are outside this generator's promised domain.

## Changes and reasons

The former 1.2.0 generator placed at most one pair per color and silently gave
up after bounded placement retries. Thus global per-color bounding boxes fit
both canonical demonstrations and all of that generated support. Several
advertised controls were ignored or clipped differently by difficulty.
The prior retained audit `review-52c1368a63326013:v0001` was a lead; its findings
were rechecked against the assigned baseline, not treated as current results.

The replacement constructs all requested pairs without placement rejection.
Only five integer axes are advertised: `grid_h` (6..20), `grid_w` (9..24),
`n_pairs` (1..4), `n_distinct_colors` (1..4), and its exact synonym
`palette_size` (1..4). Explicit color counts cannot exceed explicit pair
counts in the constructive layout. Conflicting aliases and infeasible count
requests raise errors naming the incompatible axes. Unknown axes, booleans,
coerced scalars, and out-of-range values are rejected. Removed texture,
palette-kind, density, and position labels were not reliable controls.

The earlier weak color-level validator is replaced by a shared four-connected
component analysis, strict scalar/shape checks, exact-span pairing, and
conflict checks. The `strict_canonical_like` hook means this documented expanded
bar-only manifold, not literal equality with the three canonical shapes or
with canonical object counts. Its declared minimum fraction is 1.0.

## Production curriculum and explicit overrides

Unmodified production draws cycle through three profiles by sample index:

1. `canonical_anchor`: two pairs in two colors on one of the three canonical
   canvas shapes; geometry is newly sampled, never a replayed canonical grid.
2. `even_pairs_and_span`: four bars of one color with a deliberately closest
   middle gap, plus another color's eligible outer pair and an unmatched
   middle bar shifted by one row. Three pairs are filled in total.
3. `odd_trailing_bar`: five same-span bars of one color plus another color's
   ordinary pair. Three pairs are filled, and one bar remains unpaired.

The second profile was strengthened during independent review. Its first
revision had only unmatched bars in the second color; a rival could discard
an entire color having unequal spans. The current profile forces a valid pair
and an unmatched bar to coexist in that color. Regression tests first failed
on the earlier revision, then passed after this change.

`EXAMPLES_NEEDED = 5` requests five demonstrations; the checked rotation contract
uses one query. Six consecutive
accepted pairs contain two of each profile; holding out any one pair leaves
the relevant teaching profile in the demonstrations. This is a reason for the
schedule, not a substitute for the source-bound production and rotation census.
All three start residues must be enumerated at a fixed seed as well. The exposed
solve uses five demonstrations and two queries in production order; arbitrary
simultaneous two-query holdouts are not covered by the rotation claim. Geometry,
colors and input reflections vary. Output labels always come from Racket.

Any explicit override selects the general constructive layout and honors its
exact requested measurements. These authoring draws do **not** carry the
scheduled lesson guarantee. Assemble and check such lessons separately.
Unmodified production inputs always contain two colors; difficulty primarily
changes bar heights and is not a demonstrated measure of human reasoning effort.

## Executable rivals, tests and reusable tooling

Eight declared rivals cover global color boxes, exact-span outer hulls,
rowwise filling, pairing without exact spans, greedy nearest gaps, pairing
from the right, filling only the first pair, and discarding mixed-span colors.
Each has a structural witness with a Racket-checked rival claim. All three
rival declaration namespaces contain the same eight algorithms; this does not
make twenty-four independent hypotheses.

`tests/test_regression.py` checks pixel-derived counts, boundary combinations,
strict invalid-input handling, canonical support, multi-pair/odd/mixed-span
support, determinism and mutation isolation. `workspace/probe_curriculum.py`
runs through `review.py run`, dynamically reads the actual rival declarations,
compares an independent Python interpretation with actual Racket labels,
retains exact counterexamples and source identities, and checks every local
six-draw window/query holdout. Use the public lesson census separately for
actual runner acceptance/rejection and materialized-lesson evidence.

## Limits and open findings

Finite tests against eight plausible rivals do not prove a uniquely inferable
rule, learner mastery, all-seed coverage, or training admission. The bar-only,
nonconflicting domain and two-color default are intentional restrictions.
The selected Racket authority is unchanged; archival source divergence reported
by authority-sync is not an edit made by this repair.

The shared semantic smoke gate marks every declared period as
`declared_period_not_enumerated` without ingesting a separate schedule census.
Its warning remains visible even when a matching final-source census is complete.
The return documents that tool limitation, the independent schedule evidence,
and the required maintainer decision. Prior audit resolution records remain
historical evidence; this repair does not silently mark them approved or closed.
## Current reviewer considerations

Source SHA-256: `7a54fb01857dcbd6637c26bd114eccfe103f6ef3f910b7ce777cb6233b7b5578`.

# Design decisions — d65b2dd82d74

This return repairs version 1.2.0 to 2.0.0 under unchanged assignment
`review-10591f5c6a4dc6fa`. Final generator SHA-256:
`7a54fb01857dcbd6637c26bd114eccfe103f6ef3f910b7ce777cb6233b7b5578`.
The Racket authority remains `220859949b76`. Claims below distinguish source
arguments, measured samples, and untested generalization.

## D1 — Keep the reference; make the input model respect it

The reference groups **same-color four-connected** vertical components by exact
first and last rows, then fills sorted disjoint column pairs from the left.
It leaves odd trailing bars alone and extracts objects once before painting.
The eight small authoring cases in `checks/contract-review/probe.json` checked
multiple pairs, nearest-gap disagreement, odd bars, unequal spans, singleton
and nonbar behavior, and overwrite behavior with actual Racket labels.

No reference edit was justified. The canonical inputs and selected executable
rule agree; the missing distinctions belonged to the generator. Treating equal
height as equal span, grouping every bar of a color together, or using diagonal
connectivity would change the reference. The repair uses the shared object
helper with four-connectivity stated explicitly. The separate Python oracle in
the reusable probe is only a comparison target; it never supplies training
labels in place of Racket.

The chosen domain permits contiguous vertical bars, unpaired bars, and a
same-color unmatched bar passing through a fill rectangle. It excludes nonbar
clutter, singletons, overlapping fill rectangles, and foreign-color overwrite.
Those exclusions keep the lesson focused and avoid order-dependent conflicts;
they are narrower than all inputs accepted by Racket. They are documented,
not inferred from validator acceptance alone.

## D2 — Replace the one-pair-per-color restriction

The original sampler chose one or two colors and only two bar columns per
color. A bounded retry loop could silently drop a requested pair. Its original
rationale is unknown: the starting notes were a placeholder. Retained audit
`review-52c1368a63326013:v0001`, ZIP SHA-256
`7fc74695e772952ba7cdaa3c7ac96b4c75fb7b03e05515daac237ad41d490fd3`,
was used as a lead. It was bound to the same assigned baseline generator
`feb9e2b7add32259f29f8ae990e67982624629797a8eb5c7ca48f71ea294f26f`.
Its claims were not counted as fresh measurements.

Global per-color bounding boxes therefore explained the original support.
Adding arbitrary sizes or more colors would not refute that rival. The repair
adds several same-color pairs and preserves a gap between the filled
rectangles. It also makes the *middle* gap strictly shorter than either intended
pair gap, preventing greedy nearest-gap pairing from surviving the repair.
The final seed-17/sample-1 witness in `QUESTION_ANSWER.md` is directly generated,
not merely validator-accepted or hand-authored.

## D3 — Teach odd pairing direction and exact-span selection

Four bars alone do not distinguish pairing from the left versus from the right.
A five-bar group supplies that distinction: two pairs are filled and the final
rightmost bar remains unpaired. Inputs may be reflected; labels are obtained
from Racket after reflection, so an odd-bar output is never incorrectly assumed
to be reflection-equivariant.

The first repaired even profile had a separate color consisting only of two
unmatched shifted bars. Independent review found a canonical-fitting rival
that discarded *every* color containing unequal spans. That rival also survived
those initial scheduled examples. The final profile instead puts a matched
pair at the outer columns and an unmatched shifted bar in the middle. The
eligible pair still fills, and the unmatched endpoint survives outside it.
This reverses the intermediate choice for a measured teaching reason.

Evidence preserves the sequence: `checks/tdd-mixed-span-red.log` records four
new failures on intermediate source `7f44c068d13a203ee2362260fc6a98474ac0e36f66849bc25ce06956f7fb6dcd`.
The final suite passes 85 tests. Independent final review executes 36 Racket
cases, including minimum 6×9 scheduled layouts and all four input reflections;
both ignored-span pairing and whole-color mixed-span refusal are refuted on
36/36. See `checks/code-review/REVIEW.md` and its retained commands and labels.

## D4 — Use five demonstrations and a three-profile schedule

No-override production profiles repeat by `sample_index % 3`:

| Residue | Teaching content | Realized pairs | Foreground colors |
|---|---|---:|---:|
| 0 | Ordinary pairs on a canonical-size canvas | 2 | 2 |
| 1 | Several same-key pairs, closest middle gap, valid pair plus unmatched same-color bar | 3 | 2 |
| 2 | Odd trailing bar plus ordinary second-color pair | 3 | 2 |

`EXAMPLES_NEEDED=5` requests five demonstrations. For the checked one-query
assembly, six consecutive accepted inputs contain two of each profile. Removing
any one pair leaves every profile represented. An unscheduled random mixture
was rejected because witness frequency alone cannot ensure a complete lesson;
using only three total examples would allow a query rotation to remove the only
example of a distinguishing behavior.

Actual runner evidence supports the intended assembly: final random census,
100 lessons/band, sample starts 0..99, deterministic SHA-derived seeds, no
overrides, five demonstrations plus one query. All **300/300 materialized**,
with **1,800 distinct input grids**, zero rejected draws, zero declared-rival
ambiguities, and **0/1,800 ambiguous query rotations**. The explicit seed-0
period census checks starts 0,1,2 across all three bands: **9 lessons and 54
rotations**, no rejection or ambiguity, but only **16 globally unique grids**
because its windows overlap and some bands share inputs. This is finite
fixed-seed coverage, not all-seed coverage.

The exposed solve has five demonstrations and **two** queries in production
order; it is reported separately. Arbitrarily withholding two inputs together
can remove both witnesses of a profile and is not promised. More generally,
explicit override draws enter the constructive authoring layout and do not
inherit the scheduled curriculum. Their lesson identifiability must be checked
for the actual requested assembly.

## D5 — Make advertised controls exact and observable

The original battery reported 17,039 override findings, including silently
mismatched dimensions, self-check failures, ignored controls, and acceptance
of an unknown key. Its per-band bounds disagreed with the broad declared axes.
Adding retries or relaxing the checker would leave the contract unreliable.

The new constructive shelf packing realizes every feasible tuple of dimensions,
pair count, and color count. The public axes are height 6..20, width 9..24,
pairs 1..4, and colors 1..4. `palette_size` is an exact alias for
`n_distinct_colors`, not a separate control. Contradictory aliases and more
explicit colors than pairs report structured incompatible-axis errors. Supported
values apply across difficulty bands. Unadvertised texture, density,
position-bias and palette-kind controls are removed and rejected.

Final override evidence covers **63,540 attempted draws** across 706 cases,
30 seeds/case and three bands: **61,380 accepted**, **2,160 structured
incompatibility rejections**, **0 findings and 0 warnings**. These are draws,
not unique grids or a complete high-dimensional Cartesian census. The focused
suite independently checks all ten feasible pair/color-count combinations at
both canvas boundaries across three bands, plus invalid types and alias errors.
Seed and index types are strict; determinism does not depend on global RNG state.

## D6 — Preserve canonical support without freezing geometry

One profile cycles through the canonical 9×12, 10×11 and 11×13 canvases. It
samples fresh geometry and palette, rather than replaying canonical inputs.
Other profiles range across 6..20 rows and 9..24 columns. The final profile
floor measured **8/20 easy, 6/20 medium, 7/20 hard** exact size/palette hits;
canonical validator acceptance is **3/3**. Thus teaching counterexamples no
longer crowd out canonical-sized examples.

The strict hook intentionally measures the documented expanded bar-only domain.
Its **600/600** measured acceptance does not mean 600 exact canonical profiles.
All default draws use two colors, selected uniformly without replacement from
1..9; explicit controls cover one to four colors. Difficulty mostly adjusts
bar heights, and some identical inputs occur across bands. No claim is made
that nominal difficulty has been calibrated to human or model reasoning effort.

## D7 — Keep bounded evidence and useful failures

The task-local probe dynamically enumerates all three rival namespaces rather
than copying a stale name list. There are eight unique algorithms, not 24
independent hypotheses. It compares 183 labels with actual Racket, retains the
first counterexample for every rival, and checks **165 overlapping raw
six-input windows / 990 holdouts**. These raw-window counts are distinct from
the public production census and from its unique-input counts. No independent
learner success rate is inferred from either.

The original baseline failures, the intermediate semantic warnings and
seven-rival censuses, the mixed-span red tests, and the isolated-test dependency
failure are retained. A local venv installed pytest while preserving
`PYTHONNOUSERSITE=1`; the portable test stage then passed 85/85 with zero skipped
tests. Successful intermediate results are not attributed to the final bytes.
Large evidence is stored losslessly as gzip with original/compressed hashes,
byte counts, and a restoration helper; failures are never filtered out.

## D8 — Keep the remaining shared-tool warning explicit

The final battery has **11 green stages and one nonzero stage**, semantic_gate.
The latter has no semantic errors: its sole warning is the unconditional
`declared_period_not_enumerated` status for any positive declared period.
The independent source-matched fixed-seed census completes that requested
follow-up but cannot be fed back into the smoke gate. The return therefore says
`Acceptance: needs attention` and identifies the precise acceptance decision.
The warning is not hidden, suppressed, or converted into a fictitious exit 0.
See F1 in `FEEDBACK_TO_CODEX.md`.

## Self-review of new restrictions

The intermediate mixed-span refusal shortcut was found and removed with a
concrete generated teaching case; the final eight declared rivals are refuted
in every checked production lesson and rotation. The remaining two-color,
bar-only, nonconflicting domain and five-demonstration/single-query rotation
contract are intentional restrictions, and finite evidence does not prove
universal induction, arbitrary-query assembly, or training eligibility.
