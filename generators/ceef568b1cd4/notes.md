# Working notes: ceef568b1cd4

## Review review-eb01b8c7cb621e3d — version 3.1.0

The selected 2.0.1 baseline had no associated prior review notes. This repair was
derived from that pinned source and the unchanged canonical Racket authority;
no pending predecessor repair was used as evidence.

The baseline omitted canonical-scale canvases and singletons, assigned a unique
color to every component, silently ignored several advertised controls, clamped
object counts, and had an acceptance-only validator. Its module header still
described an unrelated vertical-packing task. Four of twelve baseline battery
stages failed, with zero exact canonical profiles in sixty draws.

### Distribution decisions

Keep zero background, integer ARC colors, and the canonical same-color FOUR-
connectivity definition. The broader educational domain has 7..20 dimensions,
2..6 components, 1..6 foreground colors, areas 1..9, and both parities present.
The reference can also process empty, one-object, or one-parity inputs, but those
are outside this ordinary teaching distribution; the validator says so rather
than passing vacuous fixtures. Canonical data are all accepted.

Even sample indices draw fresh scenes with one of the four canonical dimension/
object-count profiles. Free placement permits scenes without a full blank row or
column separating the objects; bounded retries have a constructive room fallback.
Canonical-sized layouts are not canonical-grid replays. Odd indices draw five
objects in three colors: odd7/9 + even6/8 in one color, odd1/3/5 + odd1/3/5 in a
second, and even2/4 in a third. Each repeated pair touches diagonally but stays
four-disconnected. The second-color odd object touches the first-color even
object on an edge. These relations distinguish color identity, connectivity,
area extrapolation, and redundant color/diagonal-total gates.

The first repaired iteration used an odd/even repeated-color pair only. An
independent review exposed an additional canonical-fitting rule: apply true
odd-area filtering only when the color total is odd. Its three-band regression
failed on that iteration. The final odd/odd pair supplies an even color total
and an even eight-connected total while both objects must be retained. Both
conjunctions are now executable rivals. Earlier reports remain intermediate
evidence in the returned packet, never final-source evidence.

### Controls and lesson policy

Four exact integer controls are observable from returned pixels: height, width,
component count, and foreground-color count. Color count may not exceed object
count. Unknown keys, removed dummy controls, booleans, floats, and strings fail
explicitly. The inherited difficulty-hint fallback is retained; difficulty is
not an exact AXES control. Keyed RNGs and sorted set-derived choices preserve
replay across process hash seeds and call order.

Default lessons use three demonstrations and one query from consecutive indices.
Every four-index window includes two rich examples; any single holdout leaves
at least one. Explicit overrides, arbitrary subsampling, larger heldout subsets,
or external resampling require their own lesson analysis. The seven declared
rivals are a finite challenge set, not a proof against all possible rules.

`strict_canonical_like` is intentionally narrower than `self_check`: dimensions
7..8 by 7..9, 3..4 uniquely colored components, and areas at most four. Rich
scenes remain valid but are not counted as strictly canonical-like.

### Retained checks and reusable tools

Final generator SHA-256:
`1a92ce7e14e721e24bad0ac539ed9f58176b68dbcd6f4a527f0eaa90a54df78b`.
The final battery has twelve green stages with rotations required; strict
support is 336/600, canonical profile support 33/60, and all four canonical
inputs are accepted. The source-bound census has 300 lessons, 1,200 unique
inputs, and 1,200 single-query rotations with no ambiguity against seven rivals.
The 73 focused tests also pass in the portable task-test runtime. The reusable
reference probe compares 54 exact cases against the public Racket application.

Forced-fallback regressions exercise the actual seven-by-seven constructor.
The free-layout regression records 9/300 core scenes without full blank interior
row/column cuts, compared with 0/300 in the room-only draft. Shapes, color roles,
and locations vary, but rich scene composition remains deliberately structured.
There is no measurement here of model accuracy or training admission.
## Current reviewer considerations

Source SHA-256: `1a92ce7e14e721e24bad0ac539ed9f58176b68dbcd6f4a527f0eaa90a54df78b`.

# Distribution decisions — ceef568b1cd4

Final generator v3.1.0 SHA-256:
`1a92ce7e14e721e24bad0ac539ed9f58176b68dbcd6f4a527f0eaa90a54df78b`.
The pinned 2.0.1 source, canonical examples, and unchanged Racket rule were the
starting point. Associated notes were empty; original rationales not expressed
in source are unknown. No pending prior return was treated as a current result.

| Choice | Baseline / original rationale | Final decision and alternatives |
|---|---|---|
| Object identity | Distinct colors and an 8-neighbor buffer made global color counting equivalent to connected objects; the module header incorrectly described packing | Use actual same-color 4-connectivity, as the Racket primitive does. Allow same-color diagonal and cross-color edge contact. A universal 8-neighbor buffer is rejected because it removes discriminating inputs and even excludes a canonical cross-color diagonal contact. |
| Background and colors | Zero background retained; palette excluded 1 without a rule-based reason | Preserve background zero; sample foreground colors from all 1..9. Repeated color is ordinary data, not a degeneration. Exact distinct-color count is 1..6 and at most object count. |
| Canvas | Default 9..11 by 11..13; advertised lower endpoints were rejected | Exact dimensions 7..20 in every band. Half of default indices choose one of (7,8,4), (8,8,3), (7,7,3), (8,9,4), where the third entry is object/nonzero-color count. The other half vary dimensions, with band-specific weighting. |
| Object count | A drawn 3 was clamped to 4; other advertised values were not reliable | Exact 2..6. Default core has 3 or 4; default witnesses have 5. Neither requested count nor component area is silently truncated. |
| Areas | Defaults drew only 2,3,4,5; no singleton and no evidence beyond five | Broader domain areas 1..9, with all nine observed in the default regression. Core areas 1..4; rich paired areas 7/9, 6/8, two independently selected odd1/3/5 objects, and even2/4. This tests both larger odd and larger even areas. |
| Core geometry | Random growth plus separated bounding boxes; first repair used rooms throughout | Free placement precedes a total room fallback. Canonical train0 has no full blank interior cut; a regression went from 0/300 to 9/300 such core scenes. Exact full canonical grids are not replayed. |
| Rich geometry | First repair had one odd/even repeated-color pair | Final rich scenes have a diagonal odd/even pair AND a diagonal odd/odd pair of another color. An odd of the second pair edge-touches the even of the first. This simultaneously refutes seven alternatives; a seventh-row even component completes the fallback without overlap. |
| Construction failure | Bounded rejection could exhaust; source had misleading negative fixtures | Free construction is bounded, then a total seven-by-seven witness or room construction is used. Forced-fallback tests check pixels, actual component counts, and every rival. Failed partial grids are discarded atomically. |
| Exact override API | Palette/texture/density/position axes were mostly ignored | Retain four meaningful integer axes and pixel observations. Remove the five inert names and reject unknown keys. Reject bool/float/string coercion. Declare the ten impossible color-count/object-count pairs explicitly. |
| Difficulty | Existing generator treats it as a sampling hint; shared context supports numeric hints | Preserve fallback behavior for legacy hints. A test agent initially invented three rejection assertions; those were removed as a test specification error, with their failed output retained. Exact AXES validation is separate. |
| Ordinary validation | Bounds-only validator accepted blank, singleton, and destructive impostors | Enforce nonempty integer grids, declared dimensions/counts/areas, background zero, and at least one object of each parity. Empty, one-object, all-odd, and all-even scenes are Racket-lawful but intentionally outside ordinary teaching; no claim that this is the complete reference domain. |
| Strict classification | Absent before repair; first draft equated broad validity with strict support | Final strict hook recognizes the original envelope, 3..4 uniquely colored objects, and areas1..4. Final 336/600 strict support and 33/60 exact dimension/palette profiles measure distinct properties. No opt-out is used. |
| Determinism | Keyed context already present | Preserve keyed RNGs, sort set-derived choices, and return fresh grids. Tests check call-order independence and separate interpreter hash seeds. Version changes intentionally change generated streams. |

## Teaching schedule and rivals

Three demonstrations and one query use consecutive sample indices. Even indices
are core; odd indices are rich. Therefore each four-index window has two rich
inputs, and holding out any single pair leaves a rich demonstration. Core inputs
also sometimes distinguish color-blind connectivity; the rich guarantee does not
rely on that chance. Input generation is constructive and does not need a private
answer to accept or reject a lesson.

Production materialization may in general skip invalid/duplicate draws, so a
schedule argument alone is insufficient evidence. The final shared census records
all actual accepted indices, 300 complete lessons, 1,200 unique inputs and 1,200
query rotations. The focused suite additionally checks starts0..7 and all four
holdouts for actual declared predictors. This is finite evidence against the seven
rivals, not an induction theorem or a guarantee for arbitrary filtering/subsampling.
Explicit override lessons require their own review.

The initial five alternatives were global-color parity, same-color8 parity,
color-blind4 parity, keep-only-observed-odd areas1/3/5, and erase-only-observed-even
areas2/4. Independent review found that conjunction with the correct odd-area
condition could hide the first two mistakes on every original witness. Both
conjunctions now have real counterexamples in every default rich scene and are
included as pure executable predictors. No deliberately wrong solve attempt was
invented to manufacture a failure pair.

## Evidence and rejected claims

The baseline battery has four failures and two advisories. Intermediate v3.0.0
had twelve green stages and a passing five-rival census; these were insufficient
to cover the subsequently discovered conjunctions. The final source has twelve
green stages with rotations required, 73 focused/portable regressions and 54
Racket cases. All claims are source-bound; intermediate evidence is clearly
identified and preserved, including failed regressions.

The audit tasks are findings-only and unchanged. No Racket authority was edited.
No model training, inference benchmarking, approval mutation, or admission to
training was performed. Possible rules beyond the seven declared alternatives,
larger canvases/objects, arbitrary heldout subsets, and new sampling policies are
unmeasured. The maintained workspace probe is intended for later agents to replay
exact authority comparisons without reimplementing this task's tooling.
