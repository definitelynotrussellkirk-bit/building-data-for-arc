# d7f13ee34d85 — current generator decisions

Version 4.2.0, review `review-f1bc8ef6d96e32c1`. The selected Racket rule is unchanged and pinned to `435fa9a55dd3`. Generator SHA-256: `a959a4c428fb47a179bc9fccd12468dda172a45f18079952aa2630531833bd9d`.

## Intended rule and canonical evidence

Find nonzero monochrome cardinal components. A frame is exactly the border of a rectangle of height and width at least three. Sort frames by interior area and loose non-frame shapes by cell count, pair the ranks, redraw the frames, and copy the nonzero pixels of each shape's input bounding crop into its paired frame. Center at `frame_top + 1 + (interior_height - shape_height)//2` and the corresponding column. Negative offsets are intentional: canonical train pair 1 replaces the frame-border pixel at zero-based `(1,9)` from 6 to 3. Three of four canonical pairs use a negative offset; all four use one shared frame color, and three contain nonsquare frames.

The old 3.0.0 sampler used only square interiors, unique frame colors and shapes constrained to fit. Its shape sizes were always 2 through k+1. A 64-seed, index-zero diagnostic in each of default/easy/medium/hard found none of the three canonical features and found the height/perimeter ranking rivals correct on every sampled input. Both rivals also fit all four canonical pairs. Racket execution independently confirmed the canonical interpretation; a Python mirror is never used as label authority.

## Input choices and reversals

- **Frames:** 2–4 with distinct interior areas. A finite bank of portrait, landscape and square interiors replaces square-only frames. The area-witness profile requires strict rank inversions for both height and perimeter. For example, 7×2 has area 14 and dimension sum 9; 3×5 has area 15 and dimension sum 8. These frames reverse both alternatives without relying on ties.
- **Shapes:** exact connected subsets of a 3×3 box with 1–7 cells, chosen with distinct increasing sizes. The complete small normalized bank replaces capped random growth and its silent one-cell fallback. Canonical size vectors (3,4,5) and (3,4,6) are favored in the canonical profile, not required everywhere. No eight-cell hollow ring can be mistaken for a frame.
- **Centering:** `fits` keeps every rank-paired shape within the interior. `oversized` makes the smallest-ranked shape exceed at least one interior dimension by exactly one; other shapes fit. This bounds destinations within the full frame while admitting the canonical border-overwrite branch. Larger overflows remain outside this sampler.
- **Color:** frames are either all one color or pairwise distinct. Shape colors are pairwise distinct and disjoint from the frame palette; numeric colors are randomly assigned. Shared colors occur in ordinary generation and are mandatory in the default canonical profile. Background remains zero.
- **Canvas and placement:** exact heights 13–24, widths 18–28. Four frames require at least 22 columns. Two horizontal bands hold frames and shapes, with independent random horizontal orders, gaps, vertical jitter, and a random upper/lower swap. Packing is constructive and never clips or drops an object. Generation leaves one-cell gaps; validation also accepts edge-adjacent, differently colored canonical objects when their bounding crops remain disjoint.
- **Controls:** retained exact axes are `grid_h`, `grid_w`, `n_frames`, `frame_palette`, `shape_relation`. The six unused legacy descriptors/texture aliases were removed, including invalid ordinary degenerate textures. Unknown keys and wrong integer types are rejected. The only declared incompatible joint settings are `n_frames=4` with widths 18–21. A single pinned count or width selects a compatible value for the unpinned partner. One GenCtx records the actual values; `observe_overrides` recovers them from pixels.
- **Difficulty:** all bands share the legal domain and canonical support. The area profile biases frame count toward two in easy and four in hard; it does not silently restrict legal overrides. Canonical-profile inputs can repeat across bands, so reports count unique inputs explicitly.

## Teaching policy and failed iterations

Three demonstrations plus one query are drawn as four consecutive accepted pairs. A period-two schedule alternates a canonical profile (negative centering) and an area-witness profile (height and perimeter inversions). Four consecutive raw indices contain two of each; any single holdout leaves at least one of each among the three demonstrations. Broader geometry occurs within both profiles. The lesson hook requires all three declared rivals to be refuted, including after materialization; skipped or duplicate-rejected indices must not be assumed consecutive merely from the schedule proof.

Version 4.0.0 used three profiles. Its 300 ordered lessons passed, but 167/1,200 query rotations were ambiguous; this failure is retained and the three-profile choice is reversed. Version 4.1.0 fixed rotations but `(seed + sample_index) % 2` collapsed callers using `generate(sd, sd)` to one profile, hiding broad canvas sizes and difficulty variation. Version 4.2.0 hashes the seed separately before adding the index, preserving alternation while preventing that alias. The retained regression fails on 4.1.0 and passes on the final source. An earlier validator iteration incorrectly demanded a one-cell gap for canonical edge-adjacent objects; it was corrected to require disjoint crops.

`CANONICAL_SHORTCUTS` contains height and perimeter ranking, both checked against all canonical labels. `SEMANTIC_RIVALS` and `LESSON_COMPETITORS` also include clamping negative centering to zero. Witness claims are checked against actual Racket labels. Arbitrary undisclosed rivals, nonconsecutive assembly and override-specific lesson schedules remain outside the guarantee.

## Reusable checks and remaining limits

`workspace/canonical_behavior_gate.py` independently measures canonical feature support in ordinary inputs and raw consecutive windows. It records source/rule hashes, replay coordinates, denominators, unique counts and witness grids; it computes no labels. The two `counterexamples/` files retain actual Racket outputs. Tests use the portable public canonical helpers and include canonical acceptance, rival truthfulness, both schedule starts, every query position, exact overrides, packing boundaries, the seed/index alias and coverage-gate behavior.

The full return records authoritative production lesson/rotation censuses, the full battery, public task tests, independent review, solves and fresh exact-patch replay in `RESULTS.json` and `checks/`. A finite rival pass is not universal induction or training approval. The finite 3×3 shape bank, distinct sizes/areas, restricted overflow, disjoint palettes/crops, limited canvas and two-band layout are explicit distribution limits. General interleaved layouts, tied ranks, nested shapes and large overflows are not claimed. No unresolved blocker is being concealed by the narrower contract; maintainer training approval remains unchanged.
## Current reviewer considerations

Source SHA-256: `a959a4c428fb47a179bc9fccd12468dda172a45f18079952aa2630531833bd9d`.

# Decisions — d7f13ee34d85

This review starts from the selected packet's 3.0.0 source, not a previous unintegrated patch. The placeholder notes, empty associated-notes stream and absence of a current review index/tests gave no prior reviewer rationale. No earlier return was used as evidence about this task. The original packet was verified before the new draw; completed round-one work was preserved separately.

## Rule authority and the fitting assumption

The original source comment chose square interiors to make areas distinct and sorting stable. Distinct areas are useful; squares are not required by the selected rule. The old shape-fit condition appears intended to keep the transfer inside the interior, but it excludes three of four canonical examples. We preserve distinct areas/sizes and change the fit assumption to bounded signed centering. Alternatives were to change the Racket rule to clamp the result, restrict the validator while leaving the generator unchanged, or admit arbitrary large shapes. Clamping contradicts actual canonical labels; validator-only admission supplies no training examples; unbounded overflow complicates collisions and may erase distant objects. The selected bounded one-cell overflow reproduces the canonical branch while keeping destinations within the full frame.

Actual Racket evidence, not the Python diagnostic, establishes labels. The two selected counterexamples preserve both input and output, provenance and rival predictions. No canonical or base-authority file changes are included.

## Frames, motif sizes and color roles

Square-only frames are replaced by a finite rectangular bank. An area profile filters this bank for strict height and perimeter inversions, avoiding ambiguous tie-order witnesses. Canonical geometry is favored in the other profile, with additional broad draws inside it. Retaining a third broad-only profile was initially attractive but made some query rotations remove the only rank witness. Broad variation now lives within both scheduled profiles.

The fixed sequence of motif sizes 2 through k+1 was an accidental rank cue. We now choose distinct increasing sizes among 1–7, with canonical vectors favored where applicable. Every connected normalized subset of a 3×3 box in that size range is available subject to rank-paired bounds. This exact finite construction was preferred to capped growth with a size-destroying fallback. It includes multiple motifs with equal bounding boxes but different counts and all orientations that fit the box. Larger motifs, hollow eight-cell shapes and general unbounded shape growth remain outside the selected domain; their potential value is unknown.

All shape colors are distinct and disjoint from frame colors. Frame colors are all shared or all distinct. The old rationale for distinct frame colors and independently overlapping frame/shape palettes is unknown. Shared colors are canonical and prevent color alone from counting frames; distinct colors preserve additional variation. Random numeric assignment avoids making size rank equal numeric color rank. We did not add arbitrary distractors, fixed-color output conventions or a new task composition unsupported by the reference rule.

## Exact controls and constructive packing

| Choice | Original behavior/rationale | Final choice and alternatives |
|---|---|---|
| `grid_h` | Declared 10–24; actual band ranges rejected legal values | Exact 13–24 in every band; smaller layouts deliberately removed from the advertised domain |
| `grid_w` | Declared 12–28; actual band ranges were narrower | Exact 18–28, with explicit four-frame joint incompatibility below 22 |
| `n_frames` | Declared 2–4; easy/default rejected some counts | Exact 2–4 in all bands; unpinned width adapts to count |
| Palette descriptors | Six nongeometric/texture axes were ignored or accepted invalid degenerates | Replace with observable `frame_palette` and `shape_relation`; reject unknown legacy spellings instead of swallowing them |
| Placement | Repeated randomized rejection; bounded attempts could exhaust | Two constructive bands with independently shuffled orders, random gaps/jitter and upper/lower swap |
| Context provenance | Only some overrides were consumed | One GenCtx; every retained exact control is recorded and recovered from pixels |

The four-frame minimum width is a declared packing-policy limit, not a claim that every smaller lawful frame arrangement is impossible. Silently lowering frame count or clamping requested width was rejected. The full public override matrix checked 342 cases × 30 seeds × 3 bands = 30,780 attempts: 30,420 accepted plus 360 declared joint rejections, with no findings/warnings. Independent finite geometry enumeration checked all 29 count/width combinations allowed by this policy and both shape relations.

The smallest height is sufficient because the largest frame band is nine rows, the shape band at most three, and their separating gap one. Shape-band width is at most 4k−1, which fits every legal canvas. The generator leaves gaps, but the validator only requires disjoint bounding crops: canonical train pair 1 has differently colored objects touching at an edge. The initial stricter validator failed a canonical regression and was corrected.

## Demonstration schedule and query policy

Default lessons use three demonstrations and one query. The initial three-profile schedule taught all declared rivals in each ordered window, but the 300-lesson Racket census exposed 167 ambiguous query rotations. We retain that exact evidence and the four failing rotation tests. Merely declaring rotations unsupported would have been permissible; instead we changed the schedule to retain teaching evidence under every one-pair holdout without increasing context length to five demonstrations.

The two roles are a canonical negative-centering witness and an area-ranking witness. Every four consecutive raw indices contain two of each. A held-out query therefore leaves at least one of each in the three demonstrations. The lesson hook requires each named rival to be refuted. This is a sufficient finite-rival condition; it can reject arbitrary overridden or nonconsecutive lessons even when a surviving rival happens to agree on the query. It does not certify every possible program.

The initial two-slot implementation used `(seed + sample_index) % 2`. A common sampler uses `generate(sd, sd)`, so all diagonal calls became the canonical role. The defect linter caught the missing broad range/difficulty support. Version 4.2.0 hashes the seed separately into a phase before adding the index. A retained regression demonstrates the old failure; indices 0–15 on the diagonal now visit nine canonical and seven area profiles. At any fixed seed, the alternating two-plus-two argument still holds. Geometry bytes are unchanged from 4.1.0 after undoing only the recorded phase/version/import edits.

We ran the production census with query rotations required, 100 lessons per band, and separately enumerated both cyclic starts at seed zero. Final results: 300 lessons/1,200 rotations with 1,200 unique inputs, and six enumerated lessons/24 rotations with eight unique inputs; all passed. The actual sampler and accepted-index provenance are retained. Neither the raw schedule proof nor a finite sample is generalized to arbitrary rejected, duplicated or reordered streams.

## Additional gate and cost

The task-local `canonical_behavior_gate.py` measures three input features independently of generator hooks. A canonical feature missing entirely from ordinary sampling fails; lesson-target enforcement is explicit, and other lesson frequencies remain diagnostic. The baseline fails while the repaired source passes. It is inexpensive because it reads pixels and computes no labels. Existing Racket authority checks and the larger lesson census remain separate. We did not modify a shared gate or substitute this local feature extractor for a generic model-quality test.

A rare lawful branch, intentionally separate curriculum stage, or incidental canonical appearance could make a naive universal support policy produce false positives. Task-specific justification, ordinary-versus-forced counts, explicit scopes and larger follow-up samples are required. Frequency matching to the four canonical examples would be unjustified; the tool checks observed support and reports rates, not a supposed target distribution.

## Remaining domain limits and handoff

The repair preserves a finite shape/rectangle bank, distinct ranks, limited overlap, disjoint color roles/crops and a two-band layout. It does not claim robustness to large motifs, ties, nested motifs, arbitrary interleaving or undeclared rivals. Difficulty changes count priors, not legal domain. Cross-band duplicates are explicitly counted. Reference labels, approval state, unrelated generators and frozen root tests remain unchanged.

Both audit targets are findings-only, with actual Racket-labelled production counterexamples and exact commands. The before-blind solve and post-repair exposed solve are separated and retain frozen revision notes. All selected task edits are frozen before the official delta is replayed in a fresh extraction; only handoff reports are updated afterward. `RESULTS.json` and `checks/handoff/` own the exact verification evidence.
