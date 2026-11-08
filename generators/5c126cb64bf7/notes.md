# Working notes: 5c126cb64bf7

Current source: version `3.1.0`, SHA-256
`13e593cd89583bfac5e5d98625ed4017f292c30500a062652dab5250b703e32c`.
Review assignment: `review-08cf970110420b7b`. Selected Racket rule
`338c27e34ee3` is unchanged; Python comparisons are authoring diagnostics, not
label authority. Imported associated notes retain their original timestamps in
`evidence/associated_notes.jsonl`. No task-specific prior review index or frozen
root test fixture was present in the pinned baseline used for this round.

## Intended relation and admitted input domain

Read panels at columns 0–4, 6–10 and 12–16. For each whole panel, crop to its
nonzero bounding box and binarize. Rotation equivalence includes 0°, 90°, 180°
and 270°, but not a reflection unless it is also a rotation. A disconnected
satellite belongs to the pattern. The 3×3 result has diagonal 8, equivalent
off-diagonal entries 2 and other entries 0, in left-to-right panel order.

The generator admits integer-color rectangular grids of height 5–9 and width
17, background/separators 0, with 3–7 monochrome nonzero cells per panel.
Foreground colors range from 1 to 9 and can repeat between panels. Booleans,
ragged rows, nonzero separators, empty/full panels and multicolor panels are
rejected. The Racket rule can process some inputs outside this narrower
generator domain; those are not silently advertised as generated support.
`strict_canonical_like` additionally requires height 5. All five labelled
canonical inputs remain admitted, including the centered plus and the example
with mixed connected and disconnected panels.

## Decisions reversed from version 2.1.1

**R1 — remove shape-count and geometry shortcuts.** The original growth process
started at the top-left cell and assigned a distinct cell count to each rotation
class. In the retained 30-seed baseline probe, counting solved 30/30 generated
grids, while it fit only 3/5 labelled canonical pairs. Reflection equivalence
fit all 5/5 canonical pairs and all 30/30 generated grids. The original rationale
for these restrictions was not recorded. Replace growth with an immutable bank
of normalized 3×3 masks of 3–7 cells plus small achiral cores with a separated
satellite. This includes canonical shape orbits without sampling canonical
grids. Required chiral mirror negatives share cell counts, bounding dimensions up to swapping height and width,
degree histograms and pairwise distances. Satellite witnesses additionally
share largest-component rotation classes and component bags under both 4- and
8-connectivity. They differ in the arrangement of the whole pattern.

**R2 — honor controls and placement.** Shapes now move freely within panels.
Palette size can be 1, 2 or 3; colors carry no class identity. Height 5 is favored
by a 10:1:1:1:1 choice over heights 5–9. Width remains exactly 17 because the
selected relation has three fixed five-column panels; `grid_w=17` is a diagnostic
compatibility control, not a claimed variable dimension. Difficulty changes
cell-count weights (easy 3–4, medium 4–5, hard 6–7), without excluding the other
supported sizes. An independent local RNG stream governs each choice.

**R3 — replace misleading override aliases with observable facts.** Exact axes:

| Axis | Supported values | Observed meaning |
| --- | --- | --- |
| `grid_h` | 5–9 | Actual row count |
| `grid_w` | 17 | Actual fixed width |
| `n_classes` | 1–3 | Distinct whole-pattern rotation classes |
| `partition` | `all_same`, `all_distinct`, `pair_01`, `pair_02`, `pair_12` | Exact equivalence partition |
| `palette_size` | 1–3 | Number of used foreground colors |
| `texture` | `connected`, `scattered`, `mixed` | Every panel 4-connected, every panel disconnected, or both types present |

Explicit class count and partition must agree. Mixed texture requires at least
two classes: it conflicts with an explicitly requested one-class/all-same grid.
A mixed-texture request alone chooses a compatible class count instead of being
rejected because of a hidden schedule default. Structured incompatibilities name
the conflicting axes. Unknown, invalid and former ignored aliases fail loudly.
The old `palette_kind`, `n_distinct_colors`, `density` and degenerate texture
names did not provide reliable exact control and are not retained as false
compatibility promises. Use `partition` to request all-same or all-distinct.

## Lesson assembly and the version 3.0.0 failure

Default assembly is nine ordered demonstrations followed by one query, using
consecutive accepted sample indices. The declared period is 10, indexed by
`(seed + sample_index) % 10`:

| Slot | Default role |
| --- | --- |
| 0, 5 | All three patterns equivalent |
| 1 | Single pair requiring a quarter-turn, with separated satellites |
| 2 | Single pair requiring a half-turn, connected patterns |
| 3, 8 | Three distinct rotation classes |
| 4, 9 | Free class count 1–3 and compatible texture |
| 6 | Single pair requiring a quarter-turn, connected patterns |
| 7 | Single pair requiring a half-turn, with separated satellites |

The matching pair is randomly assigned among the three panel pairs. A complete
period has at least two all-same, two all-distinct and four single-pair grids.
The two free slots vary their class count and can contain mixed connectivity.
Palette cardinality is constant within a seed family: `(3,3,3,1,2)[seed % 5]`;
actual color values vary. This preserves substantial canonical-palette coverage.
Global-color parsing is answer-equivalent on three-color lessons; it is refuted
on one- and two-color lessons. Surviving while agreeing with every query is not
an ambiguity. Arbitrarily changing exact controls changes the curriculum and
does not inherit the default lesson result.

**R4 — distinguish chirality from a full rotation witness.** Version 3.0.0 initially used chirality alone for core witnesses. Its twelve-stage
battery passed, but the larger public census found 2/300 ambiguous production
lessons and 17/3000 ambiguous single-query holdouts for `no_halfturn`. A chiral
S/Z tetromino can still have 180° symmetry, making an advertised half-turn
witness ineffective. Version 3.1.0 excludes this symmetry only from required
core banks. Full/free banks retain symmetric shapes, including canonical shapes.
Three exact failed lessons are regression-covered; the original failure is
retained in `counterexamples/halfturn-stabilizer-lesson.json`.

Sixteen executable pure-grid rivals are declared. Eleven are separately claimed
as canonical-fitting, and that claim is checked against all five labelled pairs.
Witness predicates support their stated rivals. The final verification records
are in the return's `checks/` and `RESULTS.json`; the source hash above identifies
the code those records must match. No claim of unique induction against every
possible rule follows from this finite rival set.

## Reusable work and remaining limits

`tests/` uses portable canonical-data helpers and an independent array-based
rotation oracle. It covers exact joint controls, malformed grids, source purity,
canonical support and every query holdout in focused schedules. The workspace
contains a command recorder and a source-bound census re-scorer that extracts
real generated counterexamples from retained Racket labels. The re-scorer does
not generate authoritative labels of its own.

The shape family is finite and does not cover every possible 5×5 pattern. Each
panel is monochrome; width is fixed. The curriculum has a known period and lower
bounds on output-class counts; order-aware or unlisted higher-level hypotheses
are not certified by the pure-grid rivals. Extra arbitrary demonstrations or
query policies outside the tested ten-pair assembly require their own check.
A minor error-taxonomy limit remains: an out-of-range class count combined with
a contradictory partition can be classified as incompatibility before range
validation; both routes reject the request and emit no grid. There is no
task-local blocker currently known from the implemented repairs;
final finite results and independent audit findings are recorded separately.


## Current owner acceptance

Accepted the scoped generator, portable tests and task-local authoring tools using the October 3 lightweight policy. All semantic batteries, Racket comparisons, censuses, solves and replay counts in the reviewer evidence remain reviewer-reported; no routine maintainer rerun or model training admission is claimed. Exact source/rule approval records bind the accepted bytes. Both random audits remain independent findings, and shared tool requests remain proposals unless separately implemented.
## Current reviewer considerations

Source SHA-256: `13e593cd89583bfac5e5d98625ed4017f292c30500a062652dab5250b703e32c`.

# Decisions — review-08cf970110420b7b

The repair concerns `5c126cb64bf7` only. Its final generator is version 3.1.0,
SHA-256 `13e593cd89583bfac5e5d98625ed4017f292c30500a062652dab5250b703e32c`.
The canonical ledger and selected Racket program are unchanged. Before,
intermediate and final measurements refer to different source hashes and are
kept separately in `checks/`.

## R1: replace growth by a finite geometric family

The baseline grew connected motifs from `(0,0)` and assigned a different cell
count to each different rotation class. No original rationale was documented.
This made counting sufficient on all 30 sampled baseline inputs, although the
same rule fits only 3/5 canonical labels. It also made each pattern occupy a
bounding-box corner, excluding the canonical centered plus. Reflection
equivalence, largest-component matching, degree statistics and distance
statistics were stronger canonical-fitting alternatives: several fit every
canonical label and every sampled baseline input.

The replacement uses immutable normalized rotation orbits from 3×3 binary masks
with 3–7 cells, plus specified small cores with one separated satellite in a
5×5 footprint. It does not cache generated grids or random state. All canonical
shape orbits are included. Connected and disconnected cases share the same
whole-panel rule; mixed connectivity is available when there are multiple
rotation classes. The distinct-class choice excludes already-used rotation
orbits, so exact class counts do not rely on a rejection loop.

The required negative is a chiral shape and its mirror. They have equal cell
counts and reflection-invariant statistics but different rotation classes.
Satellite negatives additionally preserve the rotation classes of the unique
largest components, and preserve the component bags, under both 4- and
8-connectivity. The intended relation still distinguishes the entire pattern's
arrangement. The authored composite counterexample is retained in
`repo/generators/5c126cb64bf7/counterexamples/whole-pattern-composite.json`;
its actual output comes from `checks/repair-analysis/composite_authority.json`.

Rejected alternatives: merely adding more cell-count values preserves the
counting shortcut; random independent patterns make convincing equal-count
matches too rare; matching only the largest component changes the task;
unrestricted random 5×5 masks add considerable noise and cost without a clear
lesson benefit. The chosen finite family is intentionally bounded. It supports
the observed canonical shapes and adversarial distinctions, not every possible
5×5 pattern.

## R2: separate pattern identity from position and color

Each pattern is translated independently within its five-column panel. Rotation
is compared after cropping the whole binary pattern, so panel offset is
irrelevant. Foreground colors are sampled from 1–9 and can repeat across panels;
panel order remains spatial. Output colors 8 and 2 retain their fixed meanings.
The baseline's three different foreground colors were a canonical-like choice
but made a global color-group parser indistinguishable from a panel parser.

The default palette cardinality is `(3,3,3,1,2)[seed % 5]`, constant within each
lesson seed. Actual values and panel assignments vary independently. This gives
three-color lessons substantial support while also making color-group parsing
fail on repeated-color lessons. A color-group rival that survives a three-color
lesson agrees with its query: it is recorded as `survived_all`, not ambiguous.
This deliberate palette-family restriction is disclosed rather than treated as
a proof that every concept is separately identifiable in every lesson.

Input width stays 17 because the task has three fixed five-column panels and two
separator columns. Height varies from 5 to 9, with height 5 favored by weights
10:1:1:1:1. The final 60-draw canonical size/palette check had 24 hits: easy 5/20,
medium 13/20 and hard 6/20. The broader strict-height predicate accepted 427/600
generated inputs (71.17%) and all 5/5 canonical inputs. These are different
metrics: the strict predicate also permits repeated foreground colors.

Difficulty changes positive cell-count weights: easy favors 3–4 cells, medium
4–5 and hard 6–7. Other admitted cell counts remain possible in every band.
Increasing grid width would change the panel interpretation; using many more
cells would abandon the stated small-pattern domain. Neither was needed to
repair the demonstrated shortcuts.

## R3: exact controls and validation

Every advertised exact axis corresponds to an observable rendered fact:
`grid_h`, fixed diagnostic `grid_w`, `n_classes`, exact `partition`,
`palette_size`, and `texture`. Explicit class count and partition must agree.
Mixed texture requires multiple rotation classes, because rotated copies of one
shape cannot differ in connectivity. If the caller requests only mixed texture,
the generator chooses a compatible class count. Hidden schedule defaults do not
turn a valid single-axis request into an error.

Unknown axes and invalid enum/type/range values are rejected. Former ignored
aliases and degenerate texture names were removed; retaining them would promise
behavior the baseline did not implement. `partition=all_distinct` replaces the
misleading `no_pairs` texture, whose baseline horizontal/vertical line pair was
actually rotation-equivalent. The checker now rejects nonzero separator columns,
malformed grids, booleans, empty panels, full one-color panels and multicolor
panels. Some rejected grids are processable by Racket, but they lie outside the
generator's stated input domain.

The final public override matrix tried 184 cases × 30 seeds × 3 bands = 16,560
attempts. It accepted 15,480 and explicitly rejected 1,080 contradictory requests,
with zero findings or warnings. The independent tests add 504 valid joint-control
combinations and structured mixed/one-class rejection cases. A minor remaining
taxonomy issue is that an invalid class count combined with a contradictory
partition may raise `IncompatibleOverrides` before an out-of-range error. Both
reject the input and generate no grid; this does not affect authority or labels.

## R4: nine demonstrations, one query, and actual witness redundancy

The intended assembly uses ten consecutive accepted pairs, nine demonstrations
in their sampled order and one production query at the end. The actual period
is 10. Slots 0/5 are all-same, 3/8 all-distinct, 1/6 require quarter-turns, and 2/7
require half-turns; both rotation types have a connected and a satellite case.
Slots 4/9 freely choose class count 1–3 and compatible texture. Matching panel
pairs are randomly assigned. This supplies repeated evidence for the declared
alternatives and removes the former exact five-step output-class pattern.

The initial repaired source, version 3.0.0, passed all twelve stages and 499
corrected local tests. Its larger census nevertheless found 2/300 ambiguous
production lessons and 17/3000 ambiguous query holdouts. A chiral S/Z tetromino
can be unchanged by a half-turn, so a nominal half-turn witness did not always
distinguish `no_halfturn`. Seed 5, easy, indices 0–9 with index 2 held out is a
small reproducer. Two further failing production seeds were 3944080271/easy/start
27 and 1873861243/medium/start 45.

Version 3.1.0 excludes 180° symmetry only from the required chiral core banks.
The independent review checked four distinct orientations for all 18 connected
core templates and all 144 scattered satellite core templates. Free connected
support retains ten half-turn-symmetric templates. Restricting every shape to
asymmetric motifs was rejected because symmetric patterns are part of the task.
The old seed now contains four half-turn refutations and passes all ten holdouts.
All three failing lessons have independent regression checks.

Final source results: 300/300 production lessons, 3,000 unique input pairs, zero
production ambiguities, and zero ambiguities over 3,000 single-query holdouts.
The census uses 100 deterministic replay seeds per band, indices 0–99, with the
seed recipe and actual accepted indices retained in its source-bound report.
It tests sixteen distinct declared pure-grid competitors; repeated declaration
namespaces do not turn that into 43 independent hypotheses.

Three additional public schedule censuses enumerate starts 0–9, each band, at
seeds 0, 3 and 4, covering all palette-cardinality families. All 90 production
windows and 900 holdouts pass. These overlapping windows contain 167 unique
inputs in total (54, 57 and 56 per seed). Enumeration is exhaustive over those
fixed starts/seeds/bands, not over all generator seeds. The default policy allows
holding out any one of the ten labelled pairs while retaining the other nine
in order. Arbitrary pinned overrides can replace scheduled witnesses and do not
inherit this lesson result.

## Evidence discipline and alternatives corrected during review

The first five regression failures were intentional RED checks of actual
baseline defects, not failed solver attempts. A later test revision mistakenly
required every rival to be refuted at least twice, even if it agreed on every
pair. Nine test failures were due to that overstrong assertion. The correction
requires a demo-consistent rival to agree with each held-out query; zero
disagreements is valid, exactly one is ambiguous. Both test versions and both
result sets remain retained. Five further RED failures then captured the real
half-turn, mixed-connectivity and free-class limitations before version 3.1.0.

Authoring Racket calls, independent Python oracles, semantic contracts and
visible-only solves serve different purposes. Only retained public Racket
results are called authoritative labels. The fresh solve uses the final source with nine demonstrations and two private
queries; the census uses nine demonstrations and one query. The solve does not
reveal or independently score private query answers. Earlier parent
rule exposure is disclosed. No fake failed solve, private-label inspection,
audit-target edit or shared-runtime repair is included.

## Self-review and open limits

The repair removes several count, color, reflection and component shortcuts,
but its finite shape bank and scheduled witness slots remain distribution
restrictions. Pure-grid rival checks do not exclude order-aware curriculum
strategies, unlisted rules, arbitrary overrides or alternative lesson assembly;
the retained reports quantify the tested scope without asserting general
identifiability or changing catalog approval.

## 2026-10-25 native parametric extension

The reviewed version 3.1.0 base and canonical Racket source remain unchanged.
The nearby alternate intentionally turns the previously audited
`largest_4_component` shortcut into a separate episode-level rule rather than
weakening the canonical generator. Step A extracts and normalizes each panel's
unique largest four-connected component. Step B consumes that ordered triple and
builds the same 3×3 rotation-equivalence matrix.

The second minimum demonstration uses three deliberately related panels: two
whole patterns share the same chiral L-shaped largest component, while the third
is a reflection of the first. Their whole-pattern, largest-component,
rotation-or-reflection and cell-count matrices are all different. Together with
an all-equivalent first demonstration, this refutes the two declared settings'
most plausible named shortcuts without increasing the minimum beyond two.

The adapter supports 2–6 demonstrations and 1–4 queries with setting-matched,
prefix-stable inputs. Each panel is monochrome and has a unique largest
component. The last query spans rows 0 and 29 of a 30×17 grid and keeps both
separator columns empty. Protected Racket authoring preflight executes both
settings; the retained wrong-intermediate witness replaces Step A's component
triple with whole-panel patterns and changes the final relation matrix. These
receipts do not alter catalog approval or admit the variant to training.
