# Working notes: 2f58238f8bb6

## Repair 3.0.0

The 2.0.1 rewrite fixed the earlier empty-key/body crash but kept incompatible
canvas ranges, ignored palette controls, permissive validation, and independent
sampling that could leave key mappings unidentified. The pinned baseline source
was `fe1c9c0a903552d997ce36a8ec8e21d454bab1a3b25085f6ff930c0c2c6845a1`.
No prior selected-task return was present; the imported associated-notes file was empty.
The current Racket authority is unchanged, with normalized hash `6da56985f4bc`.

## Construction and exact controls

Inputs have 6..14 rows, 8..16 columns, 1..6 key cells, and one monochrome template
whose color is 1..9. The background remains 0 and header codes remain 1..4:
global palette relabeling would change the rule. `n` counts key cells, including
touching duplicates. `observe_overrides` derives every exact value from pixels.
Unknown names, invalid ranges, booleans, strings, and floats fail explicitly;
`None` means use the default. All four controls compose in all difficulty bands.

A bounded frontier growth process constructs 3..12 connected cells within a
4x4 box; it never clips a motif. A blank row 1 separates the header and body.
With six keys, the maximum output is 4x29. Validation checks integer colors,
header grammar, separator, one monochrome 4-connected body, and shape bounds.
This is the supported training manifold, not every grid accepted by the Racket
program: multiple body components, larger templates/canvases, other key codes,
and templates touching row 1 are deliberately outside it.

The former `palette_kind`, `texture`, `position_bias`, `density`, and
`n_distinct_colors` controls were misleading and are removed. Use
`template_color` for the body color. The former invalid textures are not ordinary
training inputs; malformed-input regression tests retain negative coverage.

## Teaching schedule

Even sample indices are teaching examples: 6x8 by default, an asymmetric
nonsquare template with eight distinct D4 transforms, and five contiguous keys
containing all four codes and an adjacent repeat. Their order is nonmonotone.
Odd indices draw broader shapes, key counts 1..6, colors 1..9, and canvases with
7..14 rows. Difficulty weights template size, canvas height, and command count;
it does not restrict the override domain.

Each four-index window contains two teaching examples. Successive teaching
examples cycle body colors 1..4, and broad examples have a different height,
preventing anchor duplicates before a four-pair episode is complete. If broad
duplicates are skipped, the next teaching examples remain distinct. Thus the
first four accepted default examples still contain at least two teaching
examples, and any three of four identify the declared key/command hypotheses.
Explicit overrides can remove this property. A different downstream sampler,
fewer demonstrations, or arbitrary subsets must be checked rather than assumed.

The checker intersects eight possible D4 transforms per key using demonstration
labels. It reports a problem only when surviving maps give different query
tiles; it never consults the query label. Twelve explicit rivals additionally
test ordering, repetitions, transform errors, alignment, and separators.
The lower-level hook assumes previously validated inputs and integer ARC labels,
as supplied by the production materializer. The saved-lesson CLI enforces both
preconditions itself, including rejecting float-valued labels and missing keys.
Three rivals fit every canonical label: truncate at four keys, collapse
consecutive commands, and count header color components. Repeated-command
witnesses falsify all three with the actual Racket output.

## Retained evidence and limits

The return retains an easy seed-0 lesson where replacing key 3's 180-degree
rotation by a vertical flip fits demonstrations 0,2,3 and changes query 1 in
eight cells. This demonstrates why key presence alone is insufficient.
The source-bound final census covers 100 lessons per band, 1,200 unique inputs,
and all 1,200 single-query rotations, with no declared-rival ambiguity or
key-map warnings. This is finite evidence within the stated hypothesis class.
The class does not cover arbitrary color-conditioned or profile-conditioned
rules, and no training-value or model-score improvement has been measured.

Portable tests and Racket-labeled fixtures live in tests/ and workspace/.
Use the public task-test stage and lesson census for future edits; the main
battery does not discover task-local tests. See the return's RESULTS.json for
actual commands, source hashes, counts, and fresh-extraction replay evidence.
## Current reviewer considerations

Source SHA-256: `dc08e3b30b8942706e33e018ebaf4aeca7c4733eb3f732e601e34e6f0a46d47a`.

# Decisions for 2f58238f8bb6, version 3.0.0

Assignment: `review-6b823d984696fe37`.
Baseline generator SHA-256:
`fe1c9c0a903552d997ce36a8ec8e21d454bab1a3b25085f6ff930c0c2c6845a1`.
Final generator SHA-256:
`dc08e3b30b8942706e33e018ebaf4aeca7c4733eb3f732e601e34e6f0a46d47a`.
Selected Racket rule hash: `6da56985f4bc`, unchanged.

## Evidence used and prior rationale

The imported generator, notes, summary, canonical pairs, selected Racket rule,
public authoring contracts, and baseline battery were reviewed. The existing
notes describe version 2.0.1 as a rewrite addressing an earlier empty-key/body
crash. The packet contains no prior selected-task return, and its imported
associated-notes file is empty; intentions beyond the written notes are unknown.
The decisions below are this review's choices, not reconstructed author motives.

The canonical authority reads nonzero header cells from left to right: 1 means
identity, 2 clockwise quarter-turn, 3 half-turn, and 4 horizontal reflection.
Every cell is a command, including consecutive equal cells. It crops the body,
transforms each copy independently, and concatenates top-aligned tiles with a
single zero column between copies. Retained Racket calls establish the repeated
cell behavior independently of a Python preview. The selected authority already
agrees with canonical labels, so neither the canonical row nor the bound or
archival Racket source was changed.

## R1: make the parameter contract describe actual input pixels

| Exact control | Supported values in every difficulty | Observable meaning |
| --- | --- | --- |
| `grid_h` | Integers 6..14 | Number of input rows |
| `grid_w` | Integers 8..16 | Number of input columns |
| `n` | Integers 1..6 | Number of nonzero header cells, including touching duplicates |
| `template_color` | Integers 1..9 | Color of the monochrome body |

All joint combinations are supported. Unknown names, out-of-range values,
booleans, floats, and strings fail explicitly instead of being clipped or
coerced. `None` requests the default. `observe_overrides` reads the actual grid
to report those four controls.

The old `palette_kind`, `texture`, `position_bias`, `density`, and
`n_distinct_colors` interfaces were removed because they advertised semantics
the construction did not reliably provide. A whole-grid palette permutation
would alter the numeric header commands, so the replacement exposes the body
color directly. Background remains 0 and key codes remain 1..4. The version
increments to 3.0.0 because callers using removed names must migrate rather
than silently receive unrelated behavior. Former malformed texture modes are
covered by negative validator tests instead of being advertised as training
distributions.

Lowering difficulty no longer narrows an explicitly advertised override range.
It only weights default canvas height, template size, and command count. This
avoids a control that works in one band but fails or changes value in another.
The final 441-case override sweep accepted all 39,690 draws with zero findings;
the independent task tests additionally cover joint and malformed requests.

## R1: bounded construction and validation

A frontier-growth construction produces one 4-connected monochrome body of
3..12 cells within a 4x4 bounding box. The generator chooses a placement that
fits and does not clip a sampled motif. Row 1 is blank to separate header and
body, leaving enough space even on a 6x8 input. Six tiles of maximum width four,
plus five separators, yield an output no larger than **4x29**, inside the ARC
30x30 envelope.

The validator independently checks rectangular integer ARC grids, dimensions,
header grammar and key count, the blank separator, a nonempty monochrome body,
connectivity, occupied-cell count, and bounding-box limits. This defines an
intentional training manifold, not the entire set of inputs for which the
Racket implementation happens to return a grid. Multiple body components,
multicolor bodies, unknown command codes, row-1 contact, larger templates, and
larger canvases are outside this contract.

Rejected alternatives were to clip templates to fit, silently reduce `n`,
relax validation until every baseline sample passes, or advertise larger canvases
without checking composed output size. Each would hide a violated control,
alter the intended geometry, or make acceptance depend on incidental parser
tolerance. The stricter domain is stated explicitly so downstream work can
extend it deliberately.

## R2: teach transformations within each complete lesson

Correct labels alone did not make the baseline lessons informative. In the
retained easy seed-0 four-pair sample, demonstrations 0, 2, and 3 are compatible
with replacing command 3's half-turn by a vertical flip. The query at index 1
distinguishes them in eight cells. Presence of a key in demonstrations therefore
does not establish its meaning: template symmetry matters.

Every even sample index now supplies a teaching example. By default it has a
6x8 canvas, a nonsquare body with eight distinct D4 transformations, and five
contiguous header commands containing all four codes and an adjacent repeat.
The order is nonmonotone, so it also refutes sorting and set-based interpretations.
Shape resampling is bounded and has an asymmetric fallback. Odd indices supply
broader inputs: heights 7..14, widths 8..16, 1..6 commands, all nine body colors,
and both symmetric and asymmetric connected templates. Broad sampling preserves
variation that an all-teaching distribution would remove.

The production contract is **three demonstrations and one query**, using the
first four accepted pairs from a fresh default draw sequence. Every raw
four-index window contains two even-index teaching examples. Their body color
is `1 + (seed + sample_index // 2) % 4`, so successive teaching examples are
distinct; broad inputs have a different height and cannot duplicate them.
Even if a duplicate broad input is skipped, the first four accepted inputs
still contain at least two distinct teaching examples. Holding out any one
of those four leaves at least one complete teaching example among the three
demonstrations. Both start residues are supported, and retained demonstrations
keep their original relative order.

This guarantee is local to fresh default four-pair episodes. Explicit overrides
can request too few commands or remove the dimension/color separation used in
the duplicate argument. An export stage that mixes pools, takes arbitrary
subsets, uses fewer demonstrations, or applies new rejection rules must check
its actual assembled lesson. The source-bound census covers consecutive starts
0..99, 100 seeds per band from its recorded SHA-256 recipe, and all four query
choices per lesson: 300 lessons, 1,200 pairs, 1,200 unique inputs, and 1,200
rotations, with no rejections or scoring errors. This is sampled evidence plus
the stated schedule argument, not exhaustive enumeration of all seeds.

Rejected alternatives include an ordered single teaching example that must
always remain in a fixed demo slot, key-presence checks, using only asymmetric
shapes everywhere, and regenerating until individual rival frequencies look
large enough. The first breaks arbitrary holdouts; the second misses the saved
symmetry counterexample; the third loses useful broad variation; the fourth
does not prove that each lesson contains a refuting demonstration.

## R2/R3: explicit hypotheses and a reusable gate

`lesson_identifiable(demos, query)` starts with all eight D4 transforms for each
key and intersects candidates using demonstration outputs. It then asks whether
the surviving transforms produce different tiles on the query input. Multiple
maps are harmless when they all produce the same query tile, so those cases
are accepted. A test supplies a query-output trap to verify that the hook does
not read the query label.

The generator declares twelve additional command/gallery rivals covering key
truncation, collapsing repetitions, treating header components as commands,
deduplication, sorting/reversing commands, incorrect transforms, missing gaps,
and bottom alignment. Tests and census enumerate the actual declarations.
`first_four_keys`, `collapse_consecutive`, and `header_components` fit all three
usable canonical labels, so they are genuine canonical shortcuts. The retained
header `[1,1,0,4,2,0,3,0]` and asymmetric L body distinguish them: actual Racket
returns a 3x15 grid while each shortcut returns 3x12.

The standard-library CLI in
`repo/generators/2f58238f8bb6/workspace/check_lesson.py` accepts ordinary ARC
train/test JSON, validates input grids and integer demonstration labels, hashes
the source and input, and applies the mapping test without Racket execution.
Exit 0 means agreement. Exit 1 (`needs_teaching`) reports any nonempty hook
finding: this includes answer ambiguity, inconsistent demonstration mappings,
or an unsupported gallery layout. Exit 2 covers JSON/ARC-grid validation and
usage failures. The CLI rejects malformed inputs before invoking the lower-level hook;
the hook itself assumes already validated materializer inputs. It does not
independently prove supplied labels correct and does not admit data for training.
This task-local implementation is included; **F1** proposes a separate shared
integration at the final production/export assembly boundary, with finer
classification of label/grammar inconsistencies versus actual answer ambiguity.

The finite family does not cover arbitrary conditionals on color, profile,
canvas, or unseen structure, and no model evaluation was run. In particular,
small teaching canvases and fixed command coverage create observable profile
correlations. Alternate broad draws and twelve explicit rivals reduce known
shortcuts but do not establish universal identifiability or a measured
Qwen3.5-9B score improvement.

## Scope, audits, and verification decisions

The immutable audit draw selected `cf6ef609da0d` and `725513c9d0c9`; only their
findings and executable evidence are returned. A-CF6-1 is an ordinary generated
lesson whose query distinguishes an unresolved bounding-box rival. A-CF6-2 is
a no-touch branch absent from ordinary support but present in a documented
texture. A2 is an inventory shortcut throughout the inspected fixed profiles,
with a validator-accepted marker relocation outside those profile choices.
These have different implications and are not combined into a defect rate.

Portable regression tests are separate from repository tests. The official
stage copies selected source, tests, fixtures, and public helpers to an isolated
layout; tests use `reviewer_support.find_root` and `canonical_pairs`, not fixed
source-depth assumptions. A missing isolated-child pytest dependency initially
blocked that stage and three repository tests. The failed commands are retained;
an actual local virtual environment with pytest in its site-packages resolves
the dependency when `PYTHONNOUSERSITE=1`. No source was changed to bypass tests,
and no failing test was removed or converted to a skip.

The final solve is bound to the exact repaired generator hash and its earlier
exposure is disclosed. The final handoff replays the packaged patch in a fresh
extraction with its own Git root, Python environment, staged runtime, and bundled
Racket installation; the resulting command records belong in `RESULTS.json`.
All genuine failed iterations and decisive counterexamples remain available.
