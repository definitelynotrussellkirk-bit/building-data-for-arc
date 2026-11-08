# Working notes: 17f92e205b34

## Current native parametric review

Assignment `review-5689200d94201137` adds the separate native family in
`workspace/parametric/`. Its status is **reviewer ready, owner acceptance
pending**. Production v1.2.0 remains byte-identical at SHA256
`55c3fde723bb8bb8043cdf9cc255e8e1f917805b0827e556898ca230dbc3741e`;
canonical normalized rule `2b970065d6a3` is unchanged. The default program is the
exact selected string, SHA256
`9d05ccab69a663e5d2fd42b94360f173f7e91e73e15800b7d78fdccf8b2fd62f`.
The historical production results below are inherited evidence, not new runs.

`selection=all|largest|smallest` is fixed per episode. `all` performs canonical
reflection. Alternatives first complete the reflection, then recompute
same-color four-connected components and keep **all** components tied for the
largest or smallest occupied cell area. Reflection joins source fragments and
changes their relative areas; selecting source components before reflecting is
a different rule. The native causal witness uses both extrema on the first
qualified seed-0 demonstration: wrong order changes **8 and 10 cells**. The
intermediate descriptions are authored; the actual and counterfactual final
labels were independently executed and replayed by the protected runtime.

The adapter supports exact integer seeds 0..2**63-1, **3–6 demonstrations and
1–4 queries independently**. It uses one complete six-demo/four-query bank,
separate input/query-order RNG streams, identical inputs across settings, and
fresh return values. One-query generation and four-query generation have the
same first public turn. Queries are independently shuffled 14×14, 24×24,
28×28 and 30×30 scenes. The 30×30 scene has 126 occupied input cells and 198
completed cells, with actual content reaching all four boundaries. This is a
finite constructive geometry family, varied by palettes, dimensions,
transpose/180-degree isometries, block scale and matching prefilled partners;
it does not claim unrestricted topology support. The unchanged production
`size` override remains limited to 6..16; 30×30 is prototype support only.

### Two demonstrated teaching repairs

The original three-demo bank admitted an `ignore_coordinate_zero` shortcut
under seed 17: largest query index 2 differed by 36 cells, and smallest query
index 0 differed by 65. Selected boundary objects alone did not ensure that
their missing coordinate-zero reflection mattered after selection. The merger
scene now has partial squares at both opposite diagonal corners; the
color-total scene has an additional cross-corner minimum.

Independent review also found that matching occupied off-diagonal partners
appeared in queries but not the first three demonstrations. A rival that
cancelled such pairs fit the original demonstrations and failed the seed-0
first query by 6/2/4 cells for all/largest/smallest. The merger scene now includes
a matching pair inside an irregular winning component. Its preservation affects
the selected result under both extrema. Both repairs keep three demonstrations,
the query branches, and the supported isometries. Both rivals are now refuted by
the first demonstration in all six protected audited episodes.

Original lessons, programs and rival predictions remain private in
`checks/17f92e205b34/audit-r1/audit.json` and
`checks/17f92e205b34/prefilled-gap-r1.json`, with the pre-repair sampler and audit
source snapshots beside them. These are retained alternative interpretations
of the original lessons, not extra official gold answers or admitted training
items. `audit-r1` and early test receipts are superseded development evidence.

### Current checks and handoff

- `checks/17f92e205b34/native-tests-r2.xml`: 106 passing adapter/sampler cases.
- `checks/17f92e205b34/audit-tests-r2.xml`: 15 passing audit/projection cases,
  including protected literal rival checks. Together these are 121 focused tests.
- `checks/17f92e205b34/audit-r2/audit.json`: six episodes, three demonstrations
  and four queries, all settings at seeds 0/17; all 120 rival comparisons
  demo-refuted, zero errors/disagreements, 369 unique protected executions
  (405 requests, 36 cache hits), and three exact canonical pairs checked.
- `workspace/parametric/evidence/manifest.json`: current native inventory.
- `checks/17f92e205b34/qualification/`: six native jobs passed, with 78
  protected executions and only the intended declared setting surviving demos.
- `checks/17f92e205b34/causal/`: native witness construction and independent
  replay; status `reviewer_replayed`, two changed-output cases.
- `checks/17f92e205b34/preview/`: 24 exact single-query public projections.
  The verifier also rejected leaked public query answers, an orphan file and a
  missing view in disposable copies. Serialized verification does not replay
  labels or authenticate rewritten private receipts.

An independent read-only review checked the repaired rival outputs, all 11
inventory entries, 150 source bindings and five executor bindings, native
qualification/replay links, and public bytes. No remaining concrete
implementation inconsistency was found in that bounded review. Finite rival
checks do not establish universal identifiability or measured training benefit.

The existing production strict-scalar audit
`review-b234206ce6588830:v0001` remains **unresolved**; the adapter's strict
request validation does not repair that different API. The lawful-short-line
`selfcheck-minimal-impostor` decision remains a separate maintainer question.
No production battery, approval update, audit-index edit, owner acceptance or
training admission was performed. After source intake, the owner must qualify
and accept the exact integrated native source.

## Current decision

Selected version: **1.2.0**. Complete the input across the main diagonal, using
the unchanged canonical Racket authority `(overlay g (transpose g))`, rule hash
`2b970065d6a3`. On a square grid its exact output is
`out[r][c] = g[c][r] if g[c][r] != 0 else g[r][c]`.

The completion domain permits upper, lower and diagonal sources. Occupied mirror
partners must agree in color, and at least one off-diagonal source must have an
empty partner. Matching prefilled pairs are lawful when another source still
needs completion. Conflicting partners, blank grids, diagonal-only grids and
already-complete symmetric grids are excluded. Metadata never bypasses checks.
The validator accepts the three canonical inputs; the imported validator rejected
both lower-triangle training inputs. No task-specific retained `review_index.json`
was present in this packet; unrelated archival findings have not been resolved.

## Distribution and controls

Four independent, observed integer axes remain: `size=6..16`, `markers=3..12`,
`palette_size=1..3`, and `diagonal_markers=0..2`. Marker count means all occupied
input cells. Every selected foreground color occurs. All Cartesian combinations
are constructive, including the smallest grid with the maximum marker count.
Explicit `None` uses the default; booleans, strings, out-of-range values and
unknown keys are errors. The previously advertised but ineffective `grid_h`,
`grid_w`, `palette_kind`, `anchor_corner`, `asymmetry_force` and `texture` controls
are retired, an intentional compatibility change. `palette_size` is an integer;
the old advertised `"varied"` value is no longer accepted.

The four-index cycle is `teaching_core`, `teaching_broad`, `ordinary_core`,
`ordinary_broad`. With no overrides, half the raw draws use sizes 6/7, 3/4 markers
and two foreground colors. The other half retain broad support in every band;
difficulty weights larger sizes/counts without deleting smaller support. Ordinary
draws may be upper-only, lower-only or mixed, with zero to two diagonal markers.
Foreground colors are drawn from 1..9. Generated sources occupy distinct unordered
mirror orbits; matching prefilled pairs are validated but not presently sampled.

Default teaching draws contain a diagonal cell, opposite-triangle sources and a
coordinate-zero source more than two cells from the diagonal. A reserved empty
orbit opposite that anchor prevents the anti-diagonal rival from filling the
required main-diagonal destination. These choices distinguish the eight declared
competitors on a teaching draw. Explicit controls can remove individual witnesses;
the lesson results below describe the default distribution, not every override.

## Teaching and evidence

`EXAMPLES_NEEDED=3` and `LESSON_SCHEDULE_PERIOD=4`. A consecutive raw four-draw
window has two teaching examples, so holding out any one retains one. The public
materializer can skip rejected inputs; actual exported lesson evidence, rather
than the raw-index argument alone, supports the measured result. The larger
default census found no ambiguity among declared rivals in 300 three-demo,
one-query lessons and all 1,200 holdouts. A separate seed-0 census covered all four
start residues in three bands: 12 lessons, 48 holdouts, 13 unique input grids.
Both keep the remaining demonstrations in order. This is finite rival evidence,
not a universal identifiability or all-seed claim.

The final task suite has 63 passing cases, and the override battery accepted
24,750 draws over 275 cases, 30 seeds and three bands. See the return's
`checks/task-tests-final/`, `checks/after-final/`, `checks/lesson-census-final.json`
and `checks/schedule-census-final.json`; exact source hashes and commands are
retained there and in `RESULTS.json`. `workspace/probe_distribution.py` is a
reusable, declaration-driven input-support probe; it does not produce labels.

## Reversals and unresolved gate

An intermediate cycle gave canonical morphology only one dedicated slot in four.
Its profile gate measured 14/60, below the floor. Core morphology now has a slot
independent of teaching role; the final gate measures 28/60 (8/20 easy, 9/20 medium,
11/20 hard). The original was 1/60. This fixes distribution mass rather than
lowering the gate or labeling broad grids as morphologically canonical.

An intermediate seed-435 teaching draw matched the anti-diagonal rival despite
its far-edge anchor. Reserving the anchor's opposite orbit fixes this concrete
case. `counterexamples/anti-diagonal-teaching.json` retains both actual Racket
outputs and rival predictions. This was an authoring counterexample, not a claim
that a complete three-demo lesson or a natural model solve failed.

The final twelve-stage battery has **11 passing stages and one failed stage**:
the generic `selfcheck-minimal-impostor` detector flags six accepted short-line
probes. A short line with an empty mirrored destination is lawful for this rule
and has a nonidentity Racket output. The validator remains semantic rather than
rejecting a lawful shape to clear a heuristic. See
`counterexamples/lawful-short-line.json`, return `checks/domain-verification.json`
and `FEEDBACK_TO_CODEX.md` F2. Acceptance needs a maintainer decision on this
specific warning; it has not been waived or patched globally.
## Current reviewer considerations

Source SHA-256: `55c3fde723bb8bb8043cdf9cc255e8e1f917805b0827e556898ca230dbc3741e`.

# Decisions for 17f92e205b34

Assignment: `review-8a0d69faf25f4b53`. Final source:
`55c3fde723bb8bb8043cdf9cc255e8e1f917805b0827e556898ca230dbc3741e`.
The original source hash is
`e090563629680065fc92f4b085a9c4148c38861997f883d45f4d6b368ccb689c`.
The rule hash remains `2b970065d6a3`; no canonical row or reference implementation
was changed. All evidence paths below are relative to this return's `WORK`-shaped
content; source paths in the patch begin `repo/`.

## M1 — preserve the actual completion domain

The exact authority overlays the transpose on the input. Its square-grid formula
is `out[r][c] = g[c][r] if g[c][r] != 0 else g[r][c]`. The original generator
sampled the upper triangle, and its validator rejected canonical `train[0]` and
`train[1]` because they have no upper-triangle source. Those are direct canonical
contradictions, not aesthetic differences in generated examples.

The repair accepts sources in either triangle and on the diagonal. It requires
integer colors 0..9 (excluding booleans), a square grid, background 0, compatible
occupied mirror partners and at least one missing off-diagonal partner. Matching
prefilled pairs are accepted if another cell needs completion. Blank,
diagonal-only and already-complete symmetric inputs are rejected, because they
remove the completion action. Metadata such as `texture="degenerate"` cannot
turn off validation.

I rejected extending the completion domain to conflicting occupied colors. The
unrestricted authority swaps those colors; a source-preserving completion
description would be wrong on that input. The retained six-square witness with
colors 2 and 7 at `(1,3)` and `(3,1)` is rejected by the new validator, while the
actual Racket output demonstrates the swap. The domain is intentionally narrower
than every grid on which the Racket program can execute. Evidence:
`checks/final-domain-probe.json`, `checks/final-domain-racket.json` and
`checks/domain-verification.json`.

## M2 — four exact, independent controls

| Control | Range | Observable meaning |
| --- | --- | --- |
| `size` | 6..16 | Both grid dimensions. |
| `markers` | 3..12 | Total nonzero input cells, including diagonal cells. |
| `palette_size` | 1..3 | Distinct foreground colors actually present. |
| `diagonal_markers` | 0..2 | Nonzero cells with equal row and column. |

These controls do not conflict: at size 6 there are 15 off-diagonal unordered
orbits; even reserving one leaves 14, above the maximum 12 off-diagonal sources.
There are at least as many total markers as foreground colors, so every selected
color is used. Construction samples orbits without replacement, avoiding a
rejection loop. Keyed generator-context randomness retains deterministic replay.

The old `grid_h`, `grid_w`, `palette_kind`, `anchor_corner`, `asymmetry_force` and
`texture` declarations did not provide useful, enforced controls. Keeping them
would perpetuate a false API. They are explicitly retired and rejected; callers
must use the four documented controls. `palette_size="varied"` is also rejected;
omitting the key or passing `None` requests the default. Version 1.2.0 records this
intentional compatibility change. The selected override matrix covers 275 cases
across 30 seeds and three bands, 24,750 accepted draws, with no findings or
combination rejections. It is not an exhaustive enumeration of all random seeds.

## Canonical mass and broad support

The cycle at `sample_index % 4` is `teaching_core`, `teaching_broad`,
`ordinary_core`, `ordinary_broad`. The default core occupies half the raw draws
independently of whether an example is pedagogical: size 6 or 7, three or four
markers, two foreground colors. Broad draws retain all declared sizes/counts in
every band, with easy/hard weighting smaller/larger values. Ordinary draws
include upper-only, lower-only and mixed inputs, and zero to two diagonal cells.
No fixed foreground color or mandatory upper-triangle cue identifies the answer.

An intermediate version allocated only one dedicated core slot. Its actual
profile-floor result was 14/60, so I rejected that mixture and added the separate
ordinary-core slot. The final profile result is 28/60: easy 8/20, medium 9/20,
hard 11/20. The original was 1/60 with zero medium/hard hits. This repairs the
sample distribution; the profile test and its thresholds are unchanged. The
new regression failed in all three bands before the change
(`checks/profile-tdd-red.log`). The intermediate generator is retained at
`checks/intermediate-generator-1.2.0.py`, SHA
`d8900dad2c40629419e4f07a41522062c05eca15d84e551c77b1e567f34bd254`.

`strict_canonical_like` names the framework hook but measures the lawful domain.
Its 600/600 final acceptance does not imply every sample looks canonical. The
independent morphology gate and `workspace/probe_distribution.py` keep those
two claims distinct. The probe's seed-0, indices-0..199 census has 200 unique
inputs per band; no cross-band uniqueness assertion is inferred from that count.

## M3 — make the lesson expose relevant distinctions

Two deliberately incomplete reflections fit all three canonical labelled pairs:
copy only within distance two of the main diagonal, and ignore coordinate-zero
sources. Teaching draws therefore include an unmatched source on coordinate zero
at distance at least three. They also include opposite-triangle sources and one
diagonal marker by default. Five witness predicates are linked to five matching
rivals, with identity, transpose-only and anti-diagonal completion completing the
eight distinct declared competitors. The generator provides inputs; these Python
rivals never supply training labels.

The first anchor implementation still allowed another source to supply the
anchor's target under anti-diagonal reflection. Independent review found an
actual counterexample after 436 candidates: seed 435, index 1, medium, overrides
size 7, markers 5, palette size 1, diagonal markers 1. The intermediate generated
input matched the anti-diagonal rival, and the public Racket command confirmed
that result. I reserved the anchor's 180-degree opposite unordered orbit from
filler. This prevents the rival from supplying the desired reflected cell while
preserving control feasibility. The regression failed before and passes after;
both actual Racket cases and rival outputs are retained in the task's
`counterexamples/anti-diagonal-teaching.json`. This is a single authoring witness,
not evidence of a naturally failed solve or an ambiguous complete lesson.

The lesson contract uses **three demonstrations plus one query**. Every
consecutive raw four-draw window contains two default teaching draws; holding
out one leaves at least one. Materialization may skip rejected inputs, so the
exported bundle still needs actual checking. The final battery required query
rotation identifiability and passed 12 lessons and 48 rotations. The wider
Racket-labelled census materialized 300/300 lessons, 1,200 pairs and 1,200 unique
inputs. Production and every single-query holdout pass, with remaining demo
order preserved. Seeds are derived from
`sha256('lesson-census:v1:TASK:BAND:INDEX')[:8]`, requested start indices 0..99
per band; the report retains the exact instances and accepted indices.

The separate declared-period census covers starts 0, 1, 2 and 3 at fixed seed 0
in all three bands: 12 lessons, 48 pair appearances and 48 query rotations, but
only 13 unique input grids because windows overlap. No materializer rejection
was recorded in either final census. This verifies finite sampled support
against declared rivals, not all seeds, arbitrary overrides, other lesson
sizes, random rejection patterns or undeclared hypotheses. An unconditional
`lesson_identifiable` hook would overstate that evidence and was not added.

## F2 — retain lawful short lines and report the remaining failure

The final battery finishes with 11 green stages and one failed `defect_lint`
stage. Its sole finding is `selfcheck-minimal-impostor`: short-line probes were
accepted 6/6. A row segment is lawful if at least one transposed destination is
empty. The retained six-square example at row 3, columns 0..3 passes the domain
check, and actual Racket fills its missing column cells, changing the input.
There is no task-semantic reason to reject it as an impostor.

I rejected adding arbitrary disconnectedness, minimum object-count or
line-shape restrictions merely to pass a generic heuristic. Such restrictions
would narrow the intended domain without changing the underlying reasoning.
The source validator remains semantic and the gate remains visibly failed;
the maintainer must decide whether to allow a task-specific exception or improve
the generic detector. `FEEDBACK_TO_CODEX.md` F2 names the evidence and a bounded
future tooling change. No gate source or policy was modified in this return.

## Scope, solves and acceptance

Only the selected task's generator, notes, summary, tests, probe and compact
counterexamples are patched. Audit findings A9F-1, A9F-2 and AFF-1 are reproduced
but their target sources remain unchanged. The optional shared CLI patch is
separate evidence; applying the official task delta does not apply it.

Both solve episodes are finished with one real revision and 3/3 visible matches.
Blind earlier exposure is `unknown` because the wrapper printed rule-adjacent
metadata; post-repair earlier exposure is `yes` because this author repaired and
read the rule before starting that phase. Neither consulted reference source
during its solve phase. Private query scores are withheld, and these authored
logs do not claim model-token traces. Final solve identity is checked against
the exact final generator SHA. Completion of review work does not mean every
gate is green or that audit findings have been resolved.
