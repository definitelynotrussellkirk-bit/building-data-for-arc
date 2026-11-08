# Working notes: 9c3781759581

## Rule and current repair candidate

The canonical transformation crops the inclusive bounding box of **all**
color-9 cells and preserves every cell inside it. Both row and column extrema
matter. The Racket rule remains unchanged; the new `RULE_HASH` declaration pins
its existing catalog hash `a489a823697d`. Python helpers supply diagnostics and independent crop checks, while
Racket remains the output-label authority.

The previous panel/divider construction and description restricted a general
marker-box rule to a narrow arrangement. The v3.0.2 repair candidate samples
sparse main-diagonal pairs, reverse-diagonal pairs, and scattered side extrema.
Ordinary draws shrink both dimensions and contain payload inside and outside
the box. The exterior payload distinguishes this rule from cropping the bbox
of all nonzero cells; scattered extrema distinguish it from cropping between
the first and last markers in row order. A reserved zero and central payload
also make clear that the complete rectangle is copied.

Frequency checks exposed a weakness in simply alternating first and second
frequency rank: least-frequent repeated-color and least-frequent even-count
selectors still fit that earlier construction and the canonical examples.
The v3.0.2 default scattered construction therefore uses a payload color with a count
greater than the marker count, a second payload color with count exactly two,
and variable counts for additional payload colors. Default scattered samples
contain at least four distinct colors, including 0 and 9. Paired samples keep
the sparse two-marker/singleton-payload arrangement. These are targeted
counterexamples to named rivals, not a general claim that color frequency
cannot identify the markers.

## Input domain and exact controls

`self_check` and `strict_canonical_like` validate the reference-lawful input
domain: a nonempty rectangular grid with 1..30 rows and columns, literal
integer colors 0..9, and at least one 9. They accept sparse arrangements,
singleton markers, a one-row or one-column crop, and a crop equal to the whole
input. They reject malformed shapes, noninteger or out-of-range colors, and
markerless inputs. They do not require the sampler's construction features.

The sampler deliberately uses a narrower domain. Canvas dimensions are 6..30,
box dimensions are 3..28, marker count is 2..8, and the palette has 3..10
distinct colors including zero and 9. It reserves positions for recognizable
textures, retained content, and a zero cell. Default draws use two markers for
either diagonal texture and four for `scattered`.

| Override | Exact interpretation |
|---|---|
| `height`, `width` | Observed input row and column counts |
| `box_h`, `box_w` | Observed inclusive bbox dimensions of all 9s |
| `marker_count` | Total number of 9 cells |
| `n_distinct_colors` | Number of distinct colors in the whole input, including 0 and 9 |
| `texture` | `canonical_pair`, `anti_diagonal`, or `scattered`, recoverable from marker extrema |

Unpinned choices adapt to valid exact requests; pinned values are neither
clamped nor silently ignored. Unknown controls and invalid literal types or
ranges raise errors. `None` means that an axis is not pinned. Retired panel
controls are not supported.

Joint incompatibilities are explicit: a pinned box cannot exceed its canvas;
`scattered` requires at least four markers; and the requested box must have
enough marker positions after the texture's reserved positions are excluded.
The capacity check reserves two opposite corners and the center for paired
textures, or all four corners and the center for scattered texture. Feasible
full-canvas boxes are allowed and need no exterior payload. The exact
`n_distinct_colors=3` control is also allowed for scattered samples, although
it leaves only one payload color and is outside the default lesson guarantee
for the two-color frequency witnesses. Other exact overrides can likewise
change which teaching witnesses are available.

## Lessons, rivals, and evidence limits

`EXAMPLES_NEEDED=4` requests four demonstrations and is paired with a one-query,
five-pair lesson check. `LESSON_SCHEDULE_PERIOD=12` combines the input profiles
`(height, width, colors) = (8,9,5), (9,10,5), (10,10,6)` with the four-position
texture pattern `canonical_pair, scattered, anti_diagonal, scattered`.
The schedule repeats semantic roles; the actual grids remain keyed draws.
Every five consecutive default positions contain at least two scattered and
two paired positions, leaving both regimes after any single query holdout.

The nine declared rivals cover:

- Cropping all nonzero cells.
- Cropping only the first and last 9s in row order.
- Cropping the most-frequent nonzero color.
- Cropping the second-most-frequent nonzero color.
- Cropping the least-frequent repeated nonzero color.
- Cropping the least-frequent even-count nonzero color.
- Cropping marker columns while retaining every input row.
- Cropping marker rows while retaining every input column.
- Keeping only marker cells inside the cropped rectangle.

Canonical-fitting rivals retain that designation, and each declared teaching
witness is tied to its corresponding rival. Lesson checks should record both
positive demonstration refutation and every query rotation. A rival agreeing
on all pairs is `survived_all`; it is distinct from a rival fitting all
demonstrations and disagreeing with a query. The absence of measured query
ambiguity alone does not establish that every rival was refuted.

Use the final review receipts for the actual seeds, commands, Racket results,
source hashes, profile checks, and rotated-lesson outcomes. Those results apply
only to the source bytes and populations they record. Earlier-version checks
do not certify v3.0.2. Construction arguments, finite rival checks, and supported
canonical profiles do not prove all-seed identifiability or exclude arbitrary
alternative transformations.

## Inherited finding and acceptance boundary

For inherited finding `review-0243aec2b13c3f8c:v0001`, **propose resolution only
after the owner accepts the new exact-source repair evidence** and confirms
that it addresses the finding. This note does not mark the finding resolved,
clear `audit_unresolved`, or grant approval. The current candidate, its canonical
rule pin, and the accepted evidence must remain linked in the task's retained
review state. Imported associated notes remain in
`evidence/associated_notes.jsonl`.

## Separate parametric proposal

`workspace/parametric/` contains a runnable proposed extension with one hidden
episode-level parameter, `target_color` in `{2,5,9}`; the original/default value
is 9. It materializes exact Racket programs and retains complete private
episodes, public challenges without query answers, and bounded cross-setting
and query-rotation evidence. Its README gives the exact commands and scope.

This extension is **prototype/proposed and not approved**. The production
per-puzzle API continues to use the fixed canonical rule and its existing
authority checks. Acceptance of the canonical generator repair does not
approve the alternative programs or create a production parameter API.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-0243aec2b13c3f8c:v0001`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `e0092f84eb4ada64646d86dcb6eb3f159d5ec53a989c2516ea442014ce1cb83e`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Explicit repair-bound closure of old e0092f84eb4ada64646d86dcb6eb3f159d5ec53a989c2516ea442014ce1cb83e against current dc6d9c68d1fb740b525c19716e9766060b8bf959585dcfd49b6634b08ebc9876. Owner static inspection confirms self_check now validates sparse color-9 marker grids without full-height divider requirement;test_all_canonical_inputs_are_accepted and test_each_difficulty_teaches_two_dimensional_cropping directly cover prior 0/3 canonical rejection and universal column-only shortcut. Source _crop_columns_only/row-crop witnesses and period12 lesson contract now address that rival. Reviewer final34methods+6735subtests,300lessons/1500rotations withnine unique rivals,40actualRacket probe inputs andfresh13-filepatchreplay followedby same tests directly exercise repaired behavior. Source-bound checks/shortcuts-v302/report.json and task counterexamples/reference_witnesses.json retained. Intermediate frequency shortcuts separately fixed and documented;not generic acceptance or source-edit closure,not an owner runtime rerun or universal claim.

### Assessment or prior finding

## 9c3781759581

**Reproduced teaching defect — the generated domain makes a wrong column-only crop rule perfect.** Target generator SHA-256: `e0092f84eb4ada64646d86dcb6eb3f159d5ec53a989c2516ea442014ce1cb83e`.

The canonical rule crops the two-dimensional bounding box of all color-9 markers. In the three labeled canonical inputs, the markers are sparse: the correct output crops both rows and columns. The wrong rival “keep every input row, crop only between the leftmost and rightmost color-9 columns” therefore fails all 3 canonical pairs; its output heights are 8, 9, and 10 instead of the authority's 4, 6, and 6.

The generator, however, constructs color-9 markers as one or more full-height divider columns, and `self_check()` requires at least one such column. Consequently the row extent is always the whole grid, making the wrong column-only rival equal to the authority on generated data. An independent 300-draw census—100 each for easy, medium, and hard, seed `20261012`, sample indices `0..99`—found 300 valid Racket outputs, 300 validator passes, 300 unique inputs, and **300/300 exact matches for the column-only rival**. An independent bounding-box oracle also matched Racket 300/300.

Reproducer and exact canonical/generated examples: `checks/audit/9c3781759581/column_crop_shortcut.json`. Probe source: `checks/audit/9c3781759581/probe.py`. The strict audit preset additionally failed because this target declares neither task-local tests nor a semantic contract; see `checks/audit/9c3781759581-audit/result.json`. This is an audit finding only, not a repair or approval.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.

[Retained evidence](counterexamples/review-0243aec2b13c3f8c-v0001/audit_assets.json), manifest SHA-256 `bd00c84f322680cc9138cf92b55c5473733cfeb5e67df5684a3cd9bfc4f51671`.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `dc6d9c68d1fb740b525c19716e9766060b8bf959585dcfd49b6634b08ebc9876`.

# Decisions and scope — review-fd6327a013d274b7

## Authority and R1: repair the input distribution, preserve the rule

The selected authority is the canonical Racket marker-box crop, normalized hash
`a489a823697d`. It finds all color-9 cells, takes their inclusive bounding box,
and copies the subgrid. The three usable canonical pairs corroborate both row
and column cropping. The old panel/divider prose and sampler contradicted that
evidence. I replaced the task-local sampler and validator and added the missing
rule pin; I did not change the authority, shared helpers, catalog, canonical
fixtures, audit indexes or audit-target generators.

Rejected: changing the Racket program to column-only cropping would make the
old generator look consistent while changing the actual task. Rejected:
keeping full-height dividers with only random palette changes would preserve
the strongest inherited distribution shortcut. Rejected: treating two opposite
corners as the entire domain would reject lawful arrangements supported by the
existing all-marker rule. The task-local edge-case probe retains Racket outputs
for a singleton, one row, one column, only-marker grid and separated extrema.

`self_check` accepts rectangular 1..30 by 1..30 literal-integer grids with values
0..9 and at least one 9. This makes the domain explicit and rejects malformed
types safely. The sampler uses canvases 6..30 and boxes 3..28 to reserve room
for interior content, zeros, marker textures and teaching witnesses. A lawful
input need not be naturally sampled by every difficulty band or default draw.

## R2: exact observable controls, no silent coercion

Seven controls remain: height, width, box height, box width, marker count,
distinct-color count and texture. Pixel observation recovers each one. Literal
integers are required for integer axes, seeds and sample indexes; Boolean,
float and string coercions are rejected. Difficulty is exactly None/easy/medium/
hard. `None` axis values are unpinned; unknown and retired panel axes fail.

Unpinned canvas dimensions grow to accommodate a legal pinned box. Explicit
canvas/box conflicts, scattered textures with fewer than four markers, and
impossible reserved-position capacities raise an exception carrying the actual
incompatible axes. The selected 298-case override battery checks 26,820 draws:
26,460 accepted with exact values and 360 explicit expected rejections, with
zero findings or warnings. This is a finite declared plan, not a claim that all
possible joint combinations were exhaustively executed.

Full-canvas crops and exact three-color scattered samples remain supported.
Those overrides can remove exterior or two-payload-color witnesses and are
outside the default lesson promise. Silently changing them to preserve a
teaching curriculum would violate the caller's exact request. Default teaching
support and the broad authoring-control API are therefore documented separately.

## Distribution and lesson assembly

The semantic texture pattern is paired / scattered / reverse-paired /
scattered. Twelve residues combine that four-position pattern with three
canonical size/palette profiles `(8,9,5)`, `(9,10,5)`, `(10,10,6)`. Three of
each four positions use the selected small profile; the remaining position
uses a band-biased canvas and broader palette. Actual coordinates and colors
remain keyed random draws. This keeps canonical overlap while retaining
larger and more varied inputs. It does not assert an empirical 75% rate in
every sampling protocol: the final profile probe measured 40/60 exact hits.

Sparse pairs provide a close bridge to the canonical examples. Reversed pairs
break a fixed top-left/bottom-right assumption. Scattered markers contribute
distinct side extrema, so first/last row-major markers are insufficient.
Exterior payload breaks all-nonzero cropping; the reserved center and zero
show that the whole rectangle, including payload and zero cells, is copied.

`EXAMPLES_NEEDED=4`: production lessons contain four demonstrations followed
by one query. For rotation, hold out every one of those five pairs and preserve
the order of the other four. Every five consecutive default texture positions
contain at least two paired and two scattered positions, so either regime
remains after any one holdout. This construction argument explains the schedule;
the actual Racket checks remain finite evidence on named rivals and exact seeds.

The final strict smoke check covers 12 lessons / 60 rotations. The fixed-seed
census covers starts 0..11 at seed 0 in all three bands: 36 lessons / 180
rotations, but only 24 unique inputs because windows overlap and core profiles
can coincide across bands. The independent larger census covers 100 lessons
per band at requested starts 0..99, with 100 hashed seeds per band, 1,500 unique
inputs and 1,500 rotations. Both production and rotation verdicts are
`no_ambiguity_found`, with no materialization, scoring or hook errors. The
report's generic residue display defaults to modulus 6 in the larger run; the
separate declared-period census is the actual period-12 coverage evidence.

## R3: avoid replacing one frequency shortcut with another

The first generalized draft made marker frequency rank too regular. v3.0.1
alternated sparse pairs, where 9 was most frequent, with scattered markers,
where a payload color was more frequent. It passed all then-declared gates,
including 300 production lessons and 1,500 rotations against seven rivals.
Independent review nevertheless found two additional canonical-fitting rules:
crop the least-frequent repeated nonzero color or the least-frequent even-count
nonzero color, breaking ties toward the larger color. Both matched all 48
sampled v3.0.1 inputs and all three canonical pairs.

v3.0.2 retains sparse pairs but gives default scattered samples at least two
payload colors: one occurs more often than the markers and one occurs exactly
twice. Additional payload multiplicities vary within remaining capacity, and
exterior positions help ensure their boxes differ from the marker box. The
default scattered palette floor rises from three to four colors; the explicit
three-color override remains available. Claims are restricted to the nine
declared rivals, including these two new selectors.

The new positive-refutation regression failed 1,440 subtests on v3.0.1 and
passes on v3.0.2. This matters because an ambiguity-only test would permit a
rival that fits every pair. The standalone `workspace/probe_shortcuts.py`
iterates the generator's actual declarations, verifies canonical-fit claims,
executes 40 inputs through the public Racket API, and retains a generated
counterexample for every declared competitor. It can be rerun on future source
versions with a new `--out` report. It does not infer universal identifiability.

## Parametric rules: suitable, runnable, proposed

The semantic parameter is `target_color ∈ {2,5,9}`, with original/default 9.
Unlike dimensions, density or distractor count, it changes the rule's output
on the same input. The parameter is sampled once per episode; all three
demonstrations and the query use it. Input generation has independent random
draws and always provides distinguishable candidate-color boxes. Parameters,
queries, complete labels and exact programs are retained privately for audit;
public challenges contain only demonstrations and unlabeled queries.

| Setting | Retained episode seed | Exact instantiated Racket source SHA-256 |
| --- | --- | --- |
| 2 | 20261022 | `3a1cd6d72b73f050cbf1fa9cc8771ebd0d9041de1e311a1c28308ea4db922ea1` |
| 5 | 20261019 | `60aaf3d5231b97930f8d06e1fc5bbcb23f8817aa7b8e1c30d699224006f7686f` |
| 9 | 20261021 | `b81b2d102e67e39397b3bdbf949856309c850750bc5b31643d160ad69d5cfab1` |

The prototype uses the public isolated Racket verifier and includes a one-cell
execution canary. It checks all three rules on the same inputs and all four
query holdouts of each episode. The retained run records three episodes,
36 rule applications, three canaries, six production comparisons and 24 refuted
rival comparisons over 12 rotations. The 15 prototype tests are included in
the final 34-method task-test run. A separate read-only peer review found no
concrete defect within this declared prototype scope.

Rejected: treating a canvas-size knob as a rule parameter. Rejected: exposing
the hidden color or query labels in the public challenge. Rejected: publishing
or approving alternate canonical programs as a side effect of this repair.
This remains proposed, with three retained settings and finite geometric
families; model learning improvement, full support coverage and production
integration are unmeasured.

## Audits, workflow and acceptance

Both drawn audits are findings-only. A1 reproduces an accepted-domain ordering
ambiguity and retains a task-test portability blocker. A2 reproduces actual
frame-border overwrites from a natural draw and a broad declared dimension-fit
problem. Their exact evidence and limits are in `AUDIT.md`. Neither target was
patched, and no approval was changed. The maintainer should triage these
findings independently of accepting the selected task repair.

The original blind solve was completed before any task implementation was
opened. The final exposed solve was prepared only after generator bytes were
frozen; it explicitly records earlier exposure and has no during-solve reference
consultation. Each has one actual revision, visible success and unknown hidden
correctness. These work logs are assistant-authored notes, not captured
token-level conversations or log probabilities.

The existing unresolved selected-task finding is proposed for resolution after
the owner accepts this exact-source evidence. It is not silently cleared.
`Acceptance: needs attention` concerns that owner decision and the independent
audits/proposal boundary; the canonical final battery has no failing stage.
The final package retains fresh patch replay and independent-environment test
receipts, along with all before/intermediate evidence. The replay extracted
338 of 77,252 files as a declared dependency closure, verified all 13 patched
files and reran 34 tests plus 6,735 subtests with no warnings. Root reports and
evidence were added afterward; the final source patch is checked against the
replayed patch hash in `checks/replay/handoff-summary.json`. Large raw receipts
are reversible gzip streams with SHA-256 mappings and tested restoration.

## Native parametric admission review (2026-10-25)

A task-local native candidate now preserves the exact canonical color-9 crop as
`crop_policy=fixed_color_9` and adds `crop_policy=selector_parity`: count color-2
cells, map odd/even to color 5/9, then crop the selected color's inclusive bbox.
The two-demo lesson exposes both parities; four prefix-stable private queries
include a substantive 30x30 boundary case. Protected-Racket audits at seeds 0
and 17 match all labels, reject both fixed-target shortcuts, verify the public
projection hides query answers and policy/program metadata, and retain a
wrong-intermediate changed-output case. Native reviewer qualification and the
source-bound causal witness are under `checks/9c3781759581/`; owner acceptance
of the exact integrated bytes remains separate.
