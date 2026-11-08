# Review 2026-10-04 — assignment review-1ae24a2a39a36cdd

## Reproduced defects in pinned version 2.1.0

The generator description said to preserve interior pixels, but canonical Racket creates a fresh empty canvas and paints only the outline. The canonical seven-cell query failed self_check's six-cell cap. Default canvases could not match any of the three canonical 5-row profiles. Many advertised axes were ignored, including motif_size; some declared grid values failed depending on difficulty; unknown keys were accepted.

A concrete teaching defect exists at seed 0, easy, sample indices 2,3,4 -> query 5. Adding a frame while retaining original pixels fits the three demonstrations but not the query. The return retains the complete inputs, canonical Racket outputs and rival predictions in checks/baseline-ambiguity.json. Baseline source hash: 327b8a15fbd77182785683cf11fd76bcb76443422c855e09b3bbed99be65e25b.

## Repair

No Racket authority was changed. Pin the verified canonical rule hash. Use exactly observable controls, a robust validator, and bounded connected frontier growth with a constructive fallback. Alternate bent-interior and broad draws; preserve canonical-scale probability in every difficulty while allowing all documented overrides. The canonical-fitting shortcut that erases only vertical-stroke pixels is now explicitly refuted by bent-interior witnesses.

## Evidence and scope

The return reports 12/12 green battery stages, 56 focused tests, 300 production lessons plus all 1,200 query rotations without declared-rival ambiguity, and 12,288 joint-override probes. workspace/lesson_probe.py is the reusable finite-domain/lesson probe; use the public census for Racket-materialized production lessons.

The distribution deliberately remains one monochrome connected object; arbitrary disconnected or multicolor inputs are not promised. No identity-only teaching tasks are emitted. Exact size 3/4 overrides are valid single examples but need not identify the full interior-erasure operation in lessons. Border-touching shapes are common (3,315/3,600 direct draws in this probe); interior placement remains supported (285/3,600). Difficulty is a size-weighting preference, not a measured model-difficulty score.

No earlier return was used as a lead; the task's supplied notes were empty and the packet used the selected baseline. The blind solve was a separate task; the post-repair solve honestly declares earlier rule exposure. See the root REVIEW.md, DECISIONS.md, RESULTS.json, and retained solve episodes in this return.
## Current reviewer considerations

Source SHA-256: `ace5571d3576ca3cbcbd5255b9ec5c8abcd4bf6911b7f1161e3d362e2da4142e`.

# Distribution decisions — 51cb5336f078

Source: pinned v2.1.0, not an unintegrated predecessor return. No earlier return was used as a lead. Original rationale beyond the supplied comments is unknown.

| Choice | Original behavior / problem | Decision and rejected alternative | Evidence and limits |
|---|---|---|---|
| Label authority | Notes described preserving interior; canonical clears it | Keep Racket unchanged; correct the description and teach erasure explicitly. Do not change labels to agree with misleading documentation. | Three canonical pairs; baseline-ambiguity Racket receipt. |
| Canvas | Default 6..8 by 7..9 excluded every canonical profile; overrides narrower in bands than AXES | 5..12 on both dimensions, weighted canonical-scale component in all bands; all exact values retained | Profile hits easy 7/20, medium 12/20, hard 13/20; 12,288 joint-control draws. |
| Object occupancy | Hard-coded random 4..6 despite advertised motif_size; canonical query has 7 | Exact 3..18 pixels, always one 4-connected component | All 16 sizes on all 64 canvases and both endpoint colors, all three bands and both residues; seed 73. |
| Shape | Sparse random walk could make demonstrations indistinguishable from overlay | Bounded frontier growth; reject only identity shapes on broad slots; require a bent occupied interior cell on default even slots | 3,600 default draws; 3,106 contain erased interior. Arbitrary disconnected and multicolor objects are outside scope. |
| Teaching schedule | No lesson contract, accidental absence of erasure witnesses | Alternate bent-interior / broad, EXAMPLES_NEEDED=3. Do not ban all small/no-interior shapes. | Four consecutive unrejected draws have two bent witnesses, leaving at least one after any query holdout. Production census separately checks actual accepted indices. One/two-demo lessons and size-3/4 override lessons are not guaranteed. |
| Canonical shortcut | All canonical interiors lie on vertical strokes | Declare erase_vertical_stroke_only, verified against every canonical pair; bent witnesses lack both a complete vertical and horizontal stroke | All three canonical pairs fit; 60/60 checked witness firings refute it in the semantic battery. |
| Color | Palette/texture names were ignored while color was uniform | Exact color 1..9; zero fixed as background | Nine focused color tests; all colors remain possible in both curriculum components. |
| Position | Mostly interior placement | Random connected growth across the full canvas, no fixed center/corner; no misleading exact position axis | Border touched in 3,315/3,600 draws; not touched in 285. This is a real border bias, not balanced placement. |
| Controls | Cosmetic and singleton axes pretended to be exact controls | Remove palette_kind, palette_size, position_bias, n_distinct_colors, density, texture; reject unknown keys. Keep only four genuinely measurable axes. | Breaking change for callers supplying obsolete axes; intentional instead of silent no-ops. No generic infrastructure changed. |
| Degenerates | Blank/singleton/filled rectangle diagnostics bypassed ordinary generation | Keep invalid examples in tests, not as training textures | Validator catches blank, malformed, invalid-color, disconnected and identity cases. Reference-lawful identity tasks are intentionally excluded here. |
| Runtime bound | Repeated random walking; hand-coded shape fallback | At most 128 growth attempts; each growth adds one cell per iteration. A staircase fallback preserves two holes while reaching all advertised sizes | A 5x5 board minus two protected holes has 23 available cells, exceeding maximum size 18; the remaining reachable board is connected. Larger boards only add capacity. |

## Alternatives and limitations

A distribution of only 3x3 crosses would cheaply show erasure but teach a cross-specific shortcut and discard canonical support. Always using large objects would also lose small lawful cases. The chosen mixture retains small broad shapes while supplying repeated semantic witnesses. The profile component changes dimensions/count weights, not labels or colors, and does not replay canonical grids.

The independent Python test specification computes a tight frame; canonical Racket remains the only training-label authority. Four distinct rival functions are registered under multiple contract namespaces; duplicated namespace entries are not independent hypotheses. The census has 1,193 unique inputs in 1,200 materialized pairs; direct cross-band probing has 2,174 unique inputs in 3,600 draws because keyed draws can coincide across bands. The 2,400 windows overlap and their 9,600 rotations are not independent lessons.

Self-review: the alternating schedule introduces an intentional sample-index correlation; downstream filtering, reordering, or explicit size overrides can break its combinatorial guarantee, so use the actual assembled-lesson gate. The shape generator has substantial border bias but no border-only restriction; the tests and production census validate a finite declared rival family, not universal rule induction or downstream Qwen accuracy.
