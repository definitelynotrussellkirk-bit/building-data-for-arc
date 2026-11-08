# 595eebab5aea — current generator notes

Version **3.0.2**. Review `review-3a22e9b3cd66af94`. The selected Racket rule is
unchanged and pinned by `RULE_HASH = "5e9e9e076193"`. Labels still come from
Racket. Python predictions implement diagnostic rivals only.

## Intended transformation

Read the three nonzero rank colors in row 0 from left to right. Find the three
monochrome four-connected body components below the separator, sort by
`(-occupied_area, bbox_top, bbox_left)`, and recolor each cropped component with
its rank color. Stack the crops with one blank row between them. The output
width is the maximum crop width; each left offset is
`(maximum_width - crop_width) // 2`. Do not sort palette colors numerically.

## Deliberate bounded population

Canvases are 11–18 rows by 12–18 columns, background 0. Row 0 has exactly three
distinct rank-color cells; row 1 is blank. There are exactly three distinct,
non-rank body colors. Each component has 2–10 cells, fits in a 5-by-5 box, and
has a blank row or column separating its box from every other body box.
Components may have equal areas. All five stored canonical inputs are accepted.

The only exact controls are `grid_h`, `grid_w`, `area_pattern`,
`alignment_profile`, and `position_bias`. Their full declared domains apply in
every difficulty band. The observer measures them from pixels. Unknown or
retired keys and malformed values raise explicit errors; there are no declared
incompatible joint controls. Difficulty changes default size weighting, not
the legal domain of an explicit request.

This population does not attempt the reference's broader behaviors for
singleton objects, repeated body colors, touching components, variable rank
counts, or extra components. In particular it cannot teach a distinction
between grouping by unique body color and extracting components, because those
operations agree throughout this population.

## Teaching contract and distribution

The default schedule repeats every three accepted draws:

1. `varied`: exact canonical dimension anchors, arbitrary supported area ties
   and positions, narrow width gap, and newly grown connected shapes.
2. `center_and_area`: three distinct cell areas in smallest/largest/middle
   top-to-bottom order; crop widths 1, 4, and 2 or 3; nonnumeric rank colors.
3. `tie_breaks`: three same-top, five-cell pieces, left-to-right a compact
   3-by-2 piece, a 5-by-1 line, and a 2-by-4 elbow. Heights 3/5/2, widths 2/1/4,
   and box areas 6/5/8 are nonmonotone. Reflections preserve those dimensions.
   Source colors are neither numerically ascending nor descending.

`EXAMPLES_NEEDED = 5`: a production lesson is five demonstrations followed by
one query. Six consecutive default draws contain two of each profile; holding
out any single pair leaves each required scene among the demonstrations.
The contract covers the 15 declared competitors, including nine that fit every
canonical label. It is not a claim of unique induction over all hypotheses.
Custom overrides, shorter lessons, arbitrary subsampling, and multiple-query
rotations need separate teaching checks.

## Decisions reversed and evidence

The imported v2.0.0 prohibited area ties even though every canonical example
contains them, used only one shape per area with widths 2–3, advertised ignored
controls, and could silently drop a shape after capped placement attempts.
The original rationale was not recorded in the current notes. The repair
admits canonical ties, grows varied polyominoes, constructs complete placements,
and declares only measurable controls. See `REVIEW.md`, `DECISIONS.md`, and the
retained before battery in the review return.

The initial repaired tie scene accidentally supported height, width, and color
shortcuts. v3.0.1 improved it, but left a bounding-box-area shortcut. Both genuine
failed iterations are retained in `counterexamples/intermediate_tie_shortcuts.json`
and `counterexamples/intermediate_bbox_shortcut.json`. v3.0.2 supplies all the
distinguishing cues in one scene. The 37 focused regressions include the exact
failed cyclic windows and every single-pair holdout at those starts.

`workspace/probe_shortcuts.py` prepares and verifies a portable, exact centering
counterexample through the supported Racket `apply` command. It discovers the
current rival declarations instead of maintaining a separate name list.
There is no known unresolved defect in this repaired bounded contract. The two
other tasks' findings in the return are audits only; their source is unchanged.
## Current reviewer considerations

Source SHA-256: `92d329fc0fca6d59485820dc8fb544600fc521065f4b38dafe6894f85f1cb837`.

# Decisions — 595eebab5aea

Assignment: `review-3a22e9b3cd66af94`. Final source is v3.0.2,
SHA-256 `92d329fc0fca6d59485820dc8fb544600fc521065f4b38dafe6894f85f1cb837`.
The baseline was the selected packet's v2.0.0, SHA-256
`da480241c8e30bb6722853dcf5064f18277f1fdb1dd741d6c66d58eeb466417c`.
No unresolved prior review for this repair target was used as a claim about its
current behavior. Its current notes were a placeholder; historical rationale
for the implementation restrictions is therefore unknown. The 22d736100571
audit used a retained prior return only as a lead, then freshly reproduced its
specific cases; see `AUDIT.md`.

## D1 — preserve the authority, repair the sampled population

The canonical rule sorts by occupied-cell area, top, and left, uses rank colors
in row order, and floor-centers cropped shapes. Every stored canonical input
contains an area tie. The imported validator rejected all five, while the
selected Racket rule already handled them correctly. Changing the rule to
require distinct sizes would contradict the task. We kept the entire canonical
ledger unchanged, pinned `5e9e9e076193`, and repaired the input generator.

The Racket source digest is
`5e9e9e076193d4c617b94f19a81304edaf5f1401ff01db6dd0670166df3f65bd`.
Its extracted callable text digest is
`042d2fdda1b9e5420763d40cc8237949ceeaa45bb14ce7aaa627bc03c3fa7285`.
These are different serialization identities, both retained by the public
census; they are not conflicting rules. `release-battery` binds canonical
outputs, rule smoke, and authority synchronization to the final source.

## D2 — bounded lawful variation rather than an unexplained template catalog

The imported five area templates had widths only 2 or 3. Floor centering then
always has offset zero. A left-aligned stack matches all five canonical labels
and every possible original default draw, regardless of colors or placement.
More random translations of those templates cannot teach centering.

The new constructor grows four-connected polyominoes with exact area and width,
using deterministic seeded frontiers. Areas range from 2 through 10, widths and
heights through 5. Width choices reserve enough room for two blank separators.
Packing uses a finite backtracking search over columns and cannot silently
discard an object. Capped random placement followed by an unchecked failure
return was rejected because it can produce incomplete inputs.

We retain exactly three distinct body colors disjoint from three rank colors,
a blank separator row, background 0, and separated bounding boxes. These are
clear limits of the sampled task, not necessary conditions of every input the
Racket program can evaluate. Early Racket probes of repeated colors, contacts,
singletons, and smaller canvases are diagnostic authority observations only;
they do not establish support in the final bounded sampler. A future extension
would need additional role and component-extraction demonstrations.

## D3 — exact controls and full-domain overrides

The new public axes are:

| Axis | Exact observable domain |
| --- | --- |
| `grid_h` | Integer 11–18 |
| `grid_w` | Integer 12–18 |
| `area_pattern` | Three distinct areas, one tied pair, or three equal areas |
| `alignment_profile` | Observed maximum-minus-minimum crop width below 2, or at least 2 |
| `position_bias` | Three, two, or one distinct bounding-box top rows |

Every advertised combination is constructive; the incompatibility list is
empty. Difficulty affects size weighting of defaults, not whether an explicit
legal endpoint is accepted. Canvas anchors every third default draw maintain
canonical size/palette support in every band without replaying canonical grids.

The old `palette_kind`, `palette_size`, `n_distinct_colors`, `density`, and
`texture` knobs did not supply reliable exact behavior. They are removed and
now raise an unknown-axis error, rather than silently succeeding. Supporting
those controls would require a deliberate domain redesign, especially because
six distinct nonzero color roles are structural here. This is a visible API
change, documented in current notes. Booleans, floating-point dimensions,
coercible strings, invalid sample indices, and unknown names are rejected.

## D4 — teach the required distinctions in each lesson

The default contract is **five demonstrations followed by one query**. A period
of three draws repeats a varied shape scene, a distinct-area/centering scene,
and an equal-area tie scene. Six consecutive default inputs therefore contain
two copies of each profile; holding out one pair leaves every required scene
in the demonstration set. Forced examples remain randomized in colors,
dimensions, placement, shapes or reflections as appropriate.

The distinct-area scene puts smallest/largest/middle in raster order, with
widths 1, 4, and 2 or 3. It distinguishes full area sorting from raster order
and “largest then raster,” and includes an odd centering gap that separates
left, right, floor, and ceiling alignment. Rank colors are not numerically
ascending. The final tie scene contains three five-cell pieces whose ordered
heights are 3/5/2, widths 2/1/4, and bounding-box areas 6/5/8. Source colors are
neither ascending nor descending. Thus the positional order cannot coincide
with these measured geometric or numeric alternatives.

The final declarations contain nine all-canonical shortcuts and fifteen unique
lesson competitors. The same callable can appear in several framework
registries; those aliases are not counted as separate hypotheses. A correct
label for each isolated grid is insufficient: the shared public census checks
the actual ordered lesson, then every pair as the held-out query. The larger
census uses 100 requested starts per band (indices 0–99), with a deterministic
hash-derived seed for each band/index. The separate schedule census covers all
three cyclic starts at fixed seed 0 in all three bands. Overlapping windows
are not counted as independent unique inputs.

The contract does not cover fewer demonstrations, arbitrary subsampling,
multiple-query rotations, or lessons assembled from arbitrary override maps.
It does not prove uniqueness against every possible rule. The ordinary solve
episode has five demonstrations and two withheld queries; its record is a
visible-example solve, not the single-query rotation census.

## D5 — keep the genuine failed iterations

The baseline focused suite recorded **27 failures and 8 passes**. The first
repair passed 35 tests and the battery, but independent review found undeclared
taller-first, narrower-first, and ascending-source-color tie rivals. All three
fit every canonical label; retained generated lessons also fit all five
demonstrations and disagree on the query. Eighteen saved labels were checked
through Racket. Adding the regression gave **2 failures and 34 passes**.

v3.0.1 changed the scene to a T, vertical line, and horizontal line and passed
36 tests, its battery, and its declared-rival census. A further concrete check
found that same-top descending bounding-box area still fit five canonical
pairs and all demonstrations of easy seed 61/start 43, while changing query
48. The global bounding-box secondary order fit only three canonical pairs,
but also survived that generated lesson. Both were independently checked on
the same six reference-labeled inputs. The next regression yielded **2 failures
and 35 passes**.

v3.0.2 uses a compact piece, vertical line, and wide elbow. Its dimensions are
nonmonotone for each measured cue and need only nine columns including
separators. Both bbox rivals are now declared; only the all-canonical variant
is called a canonical shortcut. The focused suite passes **37 tests**. Minimal
old-source witnesses are kept in the task's two `intermediate_*` counterexample
files, and full failed probes remain in `checks/semantic-probe/`.

The finished v3.0.1 solve also remains under `checks/prior-solve/v3.0.1/`, bound
to its old source. It was not relabeled as a solve of the new bytes. A fresh
final solve was prepared, with the reviewer's earlier exposure declared.

## D6 — portable execution and a small, replayable return

The first isolated task-test preflight found that pytest was installed only in
the user site, which the runner correctly excludes. No tests ran in that
attempt. We retained the failure and built an offline stdlib environment
preparer that copies already-installed distributions into a separate venv,
then verifies isolated imports. We did not weaken the test runner's isolation.

Task tests locate roots and canonical examples through `reviewer_support`.
The return includes a dynamic shortcut probe, the offline environment helper,
and a hash-checked lossless evidence compressor/restorer. Shared source is
unchanged; reusable helpers are proposals and reviewer-side tools. Large logs
are compressed with original path, byte count and SHA-256 restoration metadata.
All failed iterations remain available. The exact packaged patch is replayed
against a fresh extraction under its own Git root, and the focused tests are
run again there. `RESULTS.json` records actual commands and retained receipts.

Final handoff completed: the corrected patch was applied to a new original
extraction under its own verified Git root, with matching generator SHA-256
and 37/37 focused tests passing again. The earlier staged package had omitted
the generator file after an overwrite failed to persist; this mandatory replay
caught the mismatch. That rejected patch and receipt remain separate from the
passing final replay. The final archive is assembled in a clean staging tree
because some obsolete files reappeared after deletion in the original workspace.
No solve report was renumbered or altered, and no validator was weakened.
