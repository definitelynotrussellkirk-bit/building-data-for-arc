# Radial Order Gallery — current generator notes

Version 2.0.0; review assignment `review-cabe59617c09e22a`.
Selected canonical rule pin: `4b56f7983d0d`. The Racket authority is unchanged.

## Executed rule and input domain

Use the first row-major color-9 cell as the anchor and exclude every color-9
component from the gallery. Other objects are monochrome four-connected
components, including separate components of the same color. Order their
bounding-box centers clockwise from up, with the Racket half-plane/cross-product
comparison and bbox upper-left tie-break. Copy padded rectangles from the whole
input, so padding may retain another object's cells or a 9.

The literal padding branches matter: a crop shorter than three rows extends
down one row; color 6 adds a left column; color 2 also adds a left column when
height is below three and width is three. Otherwise a width below three adds
a column left when the component lies left of or below the anchor, right in
the other cases. Clip at the grid bounds. Racket horizontal concatenation
truncates to the shortest crop height; it does not vertically pad crops.

Production supports 10..16 rows, 12..18 columns, and 3..5 components. Generated
shapes and placements make every padded crop exactly three rows and total
gallery width at most 30. The validator also accepts all four canonical inputs,
multiple 9s, repeated component colors, and intentional padding intrusion.
This is a bounded gallery domain, not the entire set of inputs executable by
the reference rule. The Python `_gallery_probe` is a comparison model for
witnesses/rivals only; generation never uses it to manufacture output labels.

## Controls and reversals

- Replaced the single-9 requirement with first-9 anchor semantics: canonical
  train[1] contains four 9 cells, and the baseline rejected that valid input.
- Replaced distinct-color counting with connected-component counting. Total
  `palette_size` includes 0 and 9, ranges 3..7, and has the exact alias
  `n_distinct_colors`. Unpinned component count adapts to an explicit palette.
- Removed previously advertised but ignored `palette_kind`, `position_bias`,
  `density`, and `texture`. Unknown keys now fail. Impossible pinned count and
  palette combinations, or conflicting aliases, raise a structured ValueError
  identifying only the incompatible axes. `None` remains unpinned.
- Replaced band-dependent clamping with exact observable controls across the
  full declared ranges. Easy/hard affect unpinned component-count weights;
  hard does not invent a different rule. A failed intermediate dead-band check
  led to a real count-weighting change and a regression test.
- Replaced one-row/tiny-object sampling with height-two/three shapes and
  constructive separated slots. No rejection exhaustion can silently reduce
  the requested component count. Canonical dimension/count profiles are
  weighted, with nonzero support for every declared size.

## Teaching contract and evidence

Four canonical-fitting rivals are executable: occupied-cell centroid order,
isolated-9 anchor preference, shape-based special padding, and object-only
cropping. `counterexamples/combined_contrast.json` is a constructed input with
an exact public Racket label that distinguishes all four. It is explicitly
identified as a constructed witness rather than a historical generator draw.

Ordinary unpinned production alternates a translated/recolored combined
contrast scene with scattered objects (period 2). `EXAMPLES_NEEDED=4`: each
four-demo raw window contains two contrast scenes; a five-pair window retains
at least one when any pair becomes the query. The production sampler's actual
accepted indices and duplicates are recorded by the lesson census.

Final-source validation: all 12 battery stages passed, 75 focused tests passed,
and 300 Racket-labelled lessons (100 per band, four demos plus one query) had
zero ambiguous production lessons or query rotations against the four rivals
across 1,500 rotations and 1,475 unique inputs. Fixed seed 0 also covered both
declared starts in all three bands: six lessons, 30 rotations, ten unique
inputs. Exact commands and source hashes are retained in this review return.

`workspace/probe_contract.py` is a reusable Python-only control and rival
diagnostic. It checks all 49 size pairs, compatible component/palette counts,
four bands, and both schedule parities at seed 31337, plus palette adaptation
and band frequency. Its output is not a substitute for public Racket labels.

## Limits and open questions

No remaining blocking finding was reproduced for this source. Palette 3 or 4
overrides intentionally use scattered scenes even at an even index; they are
valid individual-grid controls but are outside the four-demo teaching claim.
The recognizable contrast layout and finite shape vocabulary could admit
undeclared shortcuts. The finite censuses cover the named rivals, not universal
identifiability, all random seeds, or every future downstream lesson assembly.
Training admission remains a separate maintainer decision.

Historical associated notes remain in `evidence/associated_notes.jsonl`; they
are not measurements of this version. This review started from the pinned
baseline, with no prior task-local review index or inherited task tests.
## Current reviewer considerations

Source SHA-256: `de87b51c039662d6ddc0e3ef8a99f6868599f5a4a55d5bc0d8be7f8b03521662`.

# Distribution and implementation decisions

Task `457b4958145b`, assignment `review-cabe59617c09e22a`, generator 2.0.0.
Final generator SHA-256:
`de87b51c039662d6ddc0e3ef8a99f6868599f5a4a55d5bc0d8be7f8b03521662`.
No inherited task-local review index or task tests were present. Prior design
intent beyond the brief imported summary is unknown; source behavior and
canonical examples were measured directly.

## G1 — Preserve the executable rule and repair its input model

**Prior choice:** one color-9 hub, distinct-colored objects, small isolated
shapes. The apparent rationale was a simplified verbal gallery description;
the original notes contained no justification.

**Chosen:** use first-row-major-9 semantics, monochrome connected components,
literal color-sensitive padding, and full-grid crops. The canonical rule
already labels the canonical examples consistently, while the baseline
validator rejected train[1]'s multiple markers. Changing Racket to fit the
simplification would change the task unnecessarily. The authority pin is
`4b56f7983d0d`, exact canonical rule hash
`4b56f7983d0da0e5ec03b64f4765015a5f0e1d0fdd7eca089cdfe284c58f0632`.

**Probe:** four canonical input/output pairs; public apply on nine exploratory
inputs and 242 constructed witness-family cases; final rule smoke 120 draws;
source-bound authority and grammar checks. The independent Python comparison
model matched the constructed public labels, but Racket supplies authoritative
labels. Historical constructed receipts explicitly retain the baseline source
hash and are not represented as draws from the final generator.

**Failure mode avoided:** a second reference implementation quietly becoming
the training labeler. The sampler returns input grids only; the comparison
model exists exclusively to express rivals and witness predicates. The
post-repair solve was separately authored without importing that model.

## G1 — Use a bounded three-row gallery domain

**Chosen:** 3..5 components, shape heights two or three, padded crop height
exactly three, output width at most 30. Racket's horizontal concatenation zips
rows and truncates to the shortest crop; constructing equal-height crops
prevents accidental information loss. The validator accepts every canonical
input, repeated colors, multiple 9s and lawful crop intrusion.

**Alternatives:** unrestricted heights would expand the task toward
truncation/trimming semantics that the original gallery description does not
teach. One-row shapes would preserve the baseline's narrow distribution and
recreate height imbalance. A new vertical-padding Racket branch would be an
unjustified rule change.

**Limit:** this generator samples a rule-lawful subset. It does not claim to
cover every input on which the general executable Racket function runs.
`strict_canonical_like` measures this explicit domain rather than requiring a
single exact canonical layout. The separate profile-floor evidence prevents
that predicate from hiding absent canonical size/palette support.

## G2 — Make exact axes genuinely exact

| Control | Contract | Reason and coupling |
| --- | --- | --- |
| `grid_h` | Integer 10..16 | Full range works in every band; no hidden clamping |
| `grid_w` | Integer 12..18 | Full range accommodates constructive component slots |
| `n_components` | Integer 3..5 | Counts connected objects, including same-colored separate objects |
| `palette_size` | Integer 3..7, including 0 and 9 | Pixel-observable total color count |
| `n_distinct_colors` | Exact alias of `palette_size` | Consistent observable meaning; conflicting aliases fail |

An explicitly requested palette may increase an unpinned component count so
each requested foreground color appears. If both controls are pinned and the
palette needs more foreground colors than objects, generation raises
ValueError with the relevant `incompatible_axes`. Aliases that disagree have
their own structured exception. A broad blanket incompatibility declaration
was rejected because it could conceal a bug in a compatible value pair.

Unknown keys and invalid scalar types fail early; Python booleans are not
accepted as integer controls. Seeds are Python integers, including negatives;
sample indices are nonnegative integers. Explicit `None` remains unpinned,
matching the shared generation context. Call-order independence and absence of
cross-call state are covered by focused tests and the rule smoke check.

**Reversal:** removed fake `palette_kind`, `position_bias`, `density`, and
`texture` axes instead of perpetuating knobs that do not have defined exact
pixel observables. This is a deliberate interface cleanup: consumers using
those old keys now get a useful rejection. Palette controls, previously
advertised but ignored, now have explicit total-color semantics.

**Evidence:** final override battery 28,440 draws over 316 cases × 30 seeds ×
three bands; 26,100 accepted, 2,340 structured incompatibilities, no findings
or warnings. Independent exhaustive compatible-size/count/palette combinations
at one seed cover 4,704 scenes across both schedule parities and four bands.
These finite checks do not enumerate every seed.

## G2/G4 — Canonical weighting and difficulty

**Chosen defaults:** weight the four canonical dimension/component profiles
`(12,12,4)`, `(13,13,3)`, `(12,14,4)`, `(13,14,4)` while retaining support over
the full declared ranges. Easy adds weight to three components; hard adds
weight to five. An exact override always takes precedence over weighting.

**Probe and reversal:** the first revised implementation accidentally gave
every band identical behavior. The shared defect linter detected this, and a
focused red test confirmed equal aggregate component counts (158 vs 158) for
its deterministic easy/hard sample. The final weights fix that behavior.

Across a separate seed range 0..299, using `sample_index=seed % 10`, the
independent probe measured component counts 3/4/5 as 113/180/7 in easy and
52/180/68 in hard; default and medium were 63/229/8. These are empirical counts,
not calibrated probabilities. Difficulty controls structural variety, not a
claim about human or model accuracy. A uniform distribution was rejected
because it would reduce canonical-profile support without adding a new rule
distinction. The final profile floor has exact hits in every 20-draw band.

## G2 — Construct placements instead of retrying until exhaustion

Scattered scenes use a choice of two row slots and three column slots with at
least four cells between starts. Shapes stay in their own small footprints;
objects therefore cannot merge or collide, including repeated colors. Slot
origins, selected slots, shapes, colors, and extra 9s vary. Combined contrast
scenes have a separate proven layout with safe translations.

This is preferable to the old trial-and-drop style: pinned object and palette
counts cannot silently shrink under unlucky random placements. The cost is a
finite geometric vocabulary and some latent placement regularity. The task
tests and reusable probe check observable results rather than accepting
recorded RNG draws as evidence that a control was fulfilled.

## G3 — Teach four demonstrated ambiguities together

| Rival | Why plausible on canonical examples | Separating feature |
| --- | --- | --- |
| `centroid` | Occupied-cell center is a natural interpretation of object center | Top L crosses the angular seam only for the centroid |
| `isolated9` | A single isolated 9 looks like a special hub | Earlier 9 cluster competes with a later isolated 9 |
| `shape_special` | Canonical special colors coincide with particular shapes | Color-6 rectangle receives literal color padding |
| `object_only` | A gallery naturally suggests extracting just each object | Another 9 lies inside a retained padded crop |

Each rival fits all four canonical pairs. Fixed/random witnesses that address
only one distinction per example risk leaving a rival unrefuted after a query
rotation. Instead, one scene simultaneously distinguishes all four. Its top L,
right bar, color-6 rectangle and multiple-9 layout are translated and safely
recolored. Literal special colors 2/6 are not freely permuted into equivalent
roles; public Racket execution checks the concrete recolorings.

**Teaching policy:** ordinary unpinned production alternates combined contrast
and scattered samples with declared period 2. Four ordered demos and one query
are the supported lesson assembly. Any raw five-pair window has at least two
contrast scenes, so holding out any one retains one; production-level
rejection/duplicate handling is assessed using the actual shared sampler,
with accepted indices recorded, not inferred.

**Evidence:** 300 Racket-labelled production lessons (100 starts 0..99 per
band), 1,500 query rotations, 1,475 unique inputs; zero ambiguous cases or
materialization/scoring errors. Fixed seed 0 covers both declared start
residues, all bands and all query positions: six lessons, 30 rotations, ten
unique inputs. The test-suite's additional 48 lesson/240 rotation regression
uses Python-proxy labels and is explicitly separate from this public census.

**Limits:** the complete fixed-seed check is not all-seed enumeration. A
template-matching rival outside the four declarations could still fit this
finite shape/layout family. Palette 3/4 override grids cannot instantiate the
three foreground roles and deliberately use scattered generation, so no
teaching guarantee is made for those pinned lessons. Do not export a different
demo count or assembly policy under these evidence claims without checking it.

## Reusable tooling and stopping decision

The public packet already provides Racket execution, staged task tests, and
source-bound lesson census tools, so these were reused. The new task-local
`workspace/probe_contract.py` addresses the remaining gap: exhaustive compatible
exact-axis combinations across parities, with the current hook declarations
loaded from the generator. It requires an output path and records source,
tool, command and count provenance. It never calls its Python proxy a label
authority. The original independent review probe and receipt are also retained.

After the required gates, larger census, schedule enumeration, code review,
audits and final-patch replay, further broad testing would not resolve a named
remaining blocker. Universal induction and downstream training approval remain
outside the demonstrated result. No shared source changes were made merely to
make local checks pass; F1 proposes the one warranted shared linter improvement.
