# Working notes: b6452f922704

## Current rule/domain account

Each of exactly three equal hollow maroon frames contains one blue shape, one red shape, and one key cell directly above the frame. For each frame, take the intersection of the red and blue **bounding boxes**, emit a solid rectangle of that size in the local key color, then pack the three rectangles left-to-right with one-column gaps and floor vertical centering in the tallest output.

The selected Racket authority is unchanged and pinned by `RULE_HASH=abfc4a89f098`.

## Reversed decisions

Version 1.3.0 required globally distinct key colors and advertised generic palette/texture axes. This was reversed because all five canonical inputs repeat keys, the old `self_check` rejected every canonical pair, helpful textures were dead, negative fixtures were mixed into the ordinary domain, and several exact axes were unobservable or unenforced.

Version 2.0.0 exposes only three exact observable axes: `frame_h=6..8`, `frame_w=6..8`, and `key_variety=1..3`. Unknown or malformed overrides fail loudly. Repeated keys are lawful.

## Generator design

- Always three equal frames; this matches all canonical examples and supports a compact 3-demo lesson.
- Constructive opposed L-shapes guarantee disjoint connected red/blue shapes and chosen positive bbox intersections without rejection sampling.
- Every grid includes overlap heights 1 and at least 3, so it distinguishes vertical centering from the strongest canonical-fitting rival, `top_align`.
- Defaults favor 7x7 frames and repeated keys to anchor canonical profiles, while all boundary values remain available through defaults and exact overrides in every band.
- `observe_overrides` recovers all public axes from pixels.
- `strict_canonical_like`, witness/rival dictionaries, and `lesson_identifiable` form the executable teaching contract.

## Evidence

Final generator SHA-256: `507c68b8d9eb31fcc3a86d999854acfada8bc269438724a91b5fc4b22c7e9b4c`.

- Final battery: 12/12 green.
- Final selected-task tests: 28/28 passed.
- Profile gate: all 5 canonicals accepted; 24 exact hits in 60 draws (11 easy, 9 medium, 4 hard).
- Semantic gate: strict 600/600; centering witness 600/600.
- Larger census: 300/300 lessons, 1,200 unique pairs/rotations, zero ambiguity/errors/warnings; `top_align` refuted in every lesson.
- Exact Racket-checked witness: `counterexamples/top_align_vertical_centering.json`.
- Independent reusable geometry helper: `workspace/reference_probe.py`.

## Known limits/open findings

The sampler intentionally covers exactly three equal 6..8 frames, not every input the Racket program could process. Shapes come from a constructive opposed-L family, so heavy oversampling could expose that family. The semantic evidence is finite and only covers declared rivals; it does not prove uniqueness against every possible hypothesis. The fixed overlap-height witness schedule is learnable, although it does not determine widths, keys, order, or the correct gallery without solving the local bbox task.
## Current reviewer considerations

Source SHA-256: `507c68b8d9eb31fcc3a86d999854acfada8bc269438724a91b5fc4b22c7e9b4c`.

# Decisions for `b6452f922704`

## D1 — Treat repeated key colors as lawful

**Prior choice.** Version 1.3.0 sampled distinct key colors and `self_check` required them to be globally distinct.

**Evidence.** All five canonical inputs repeat at least one key color, and the before self-check rejected all five. Key identity is local to a frame; the Racket rule never requires global uniqueness.

**New choice.** `key_variety=1..3` explicitly controls the number of distinct colors among three keys. Variety 1 produces three equal keys, variety 2 one repeated pair, and variety 3 all distinct.

**Alternatives rejected.** Keeping distinct keys and exempting canonicals in `self_check` would leave generation outside the canonical domain and make the validator dishonest. Adding a Boolean `allow_repeats` would expose less information than the observable count and complicate exact override testing.

**Failure modes/limits.** Colors remain restricted to 3..8 because 0, 1, 2, and 9 have fixed structural roles. The generator does not currently exercise other nonstructural ARC colors if future authorities allow them.

## D2 — Generate exactly three equal frames

**Prior choice.** The old sampler emitted two or three frames. The summary and generic axes did not cleanly describe the realized structure.

**Evidence.** Every canonical pair has exactly three equal 7x7 frames. Three parts also give a compact lesson with enough room for unequal output heights and repeated-key patterns.

**New choice.** Every draw has three equal frames. `frame_h` and `frame_w` are exact axes in 6..8; all boundary values are legal in every difficulty band.

**Alternatives rejected.** Retaining two-frame lessons would broaden syntax but reduce the number of simultaneous local examples and diverge from the canonical presentation. Variable per-frame sizes would add an unneeded composition distinction and make a single exact size axis unobservable.

**Failure modes/limits.** The Racket authority can in principle process a different number of frames, so the sampler is intentionally narrower than the program. This review did not attempt to certify arbitrary frame counts.

## D3 — Replace rejection sampling with constructive opposed L-shapes

**Prior choice.** Two random polyominoes were independently grown and repeatedly placed until their bounding boxes overlapped without cell collisions.

**Evidence.** The old approach made exact overlap geometry indirect and could not guarantee a vertical-centering witness. Its public controls described chamber size rather than the task-relevant output geometry.

**New choice.** `_opposed_l_shapes` constructs two connected, disjoint L-shapes with a chosen exact bbox-overlap height and width. Whole-interior flips and color swapping retain visible variety without changing the proof.

**Alternatives rejected.** Continuing random polyomino rejection with post-filtering would make witness frequency probabilistic and introduce avoidable generation failures. Drawing filled rectangles would expose the answer too directly and reduce shape diversity.

**Failure modes/limits.** The shape family is narrower than arbitrary polyominoes. The semantic content still depends on bounding boxes rather than cell overlap, but agents could learn the fixed shape family if this task were heavily oversampled.

## D4 — Force a vertical-centering witness in every instance

**Canonical ambiguity.** The strongest plausible rival is `top_align`: compute the correct local rectangles and horizontal packing, but place every part at output row 0. It fits all five canonical pairs because no shorter part needs a positive floor-centered offset.

**New choice.** The three overlap heights always include 1 and 3 plus one lawful random height. Thus the tallest output is at least 3, and the height-1 part has center offset at least 1. Every grid refutes `top_align` once labeled.

**Alternatives rejected.** Merely increasing the chance of unequal heights would leave complete lessons probabilistically ambiguous. A scheduled witness only once per lesson would couple correctness to ordering; per-instance witnesses support every query rotation.

**Evidence.** The semantic gate found the witness in 600/600 strict draws. The 300-lesson rotated census refuted `top_align` in every production lesson and every held-out position. The exact saved witness is `counterexamples/top_align_vertical_centering.json`.

**Failure modes/limits.** This contract proves only that the declared rival is refuted. It does not enumerate all possible shortcuts. The fixed `{1,3,random}` height schedule is itself learnable, though it does not determine the correct output without parsing local keys and overlap widths.

## D5 — Keep only three exact public axes

**Prior choice.** The generator advertised `palette_kind`, `palette_size`, `position_bias`, `n_distinct_colors`, `density`, and `texture`, even though several were dead, singleton diagnostics, aliases, or included invalid negative fixtures.

**New choice.** Public `AXES` contains only `frame_h`, `frame_w`, and `key_variety`. Unknown axes and invalid types/ranges raise. `observe_overrides` recovers every axis from a valid returned grid. No ordinary incompatible combinations exist.

**Alternatives rejected.** Marking dead axes diagnostic would preserve misleading API surface. Keeping negative textures as legal ordinary values would continue mixing counterexamples with training inputs. An `overlap_height` axis was not exposed because three per-frame values cannot be recovered as one scalar without defining a more complex public schema.

**Evidence.** Final lint, defect lint, and override stages are green; focused tests exercise lower/middle/upper values in all four difficulty modes and reject unknown/malformed values.

## D6 — Weight defaults toward canonical profiles without hiding legal support

**Initial repair.** Uniform-ish default choices passed functional checks but only 16.7% of the focused 128-draw samples matched the canonical 11x25 profile, below the explicit 25% regression floor.

**New choice.** Default choice tuples favor 7x7 frames and key varieties 1 or 2 while retaining 6/8 and variety 3 in every band. Exact overrides still span the complete 6..8/1..3 domain.

**Alternatives rejected.** Hard-coding canonical 7x7 would eliminate useful lawful variation. Declaring a profile opt-out would be unjustified because exact canonical support is easy and relevant.

**Evidence.** Final profile gate records 24/60 exact hits: 11 easy, 9 medium, 4 hard, with no crashes or canonical rejections. Focused 128-draw checks per band require at least 32 canonical-profile cases and realize every axis value.

## D7 — Use strict structural validation rather than generation-history metadata

**New choice.** `_frame_records` validates rectangular ARC colors, exactly three complete hollow frames, one local key per frame, legal interiors, both shape colors, positive bbox overlap, equal frame sizes, and no stray nonzero cells. `self_check` converts parser exceptions to diagnostics; `strict_canonical_like` reuses the same structural contract.

**Alternatives rejected.** Trusting generator metadata would not validate canonical or externally supplied grids. A shallow color-count check would miss broken frames, absent keys, and stray cells.

**Failure modes/limits.** The parser expects connected maroon frame perimeters and one key in the row immediately above. That matches the selected authority and canonicals but is not a general detector for nested or touching frames.

## D8 — Keep the Racket authority unchanged

**Evidence.** The canonical Racket source already computes frame-local blue/red bbox intersections, packs them left-to-right with one-column gaps, and vertically centers them. Rule smoke and authority synchronization passed before repair; the defects were in input generation and teaching support.

**Choice.** Pin `RULE_HASH=abfc4a89f098`; do not edit canonical or base solution data.

**Failure mode avoided.** Changing the rule to top-align would fit canonical outputs but encode the very shortcut the generator must distinguish.

## D9 — Build an independent reusable probe

`workspace/reference_probe.py` intentionally does not import production generator internals. It recovers frame geometry, computes centered and top-aligned galleries, observes exact axes, and detects a vertical-centering witness. This gives future reviewers a small oracle for focused tests and counterexample construction without duplicating the Racket implementation.

The probe is still a Python mirror, not the authority. The saved counterexample was separately evaluated by the selected Racket `target_code`, and the two outputs were asserted equal.

## D10 — Lesson assembly and evidence scope

`EXAMPLES_NEEDED=3`; downstream lessons use 3 demonstrations and 1 query. Because every generated pair is a witness, ordering is not semantically required. The larger census therefore used `--rotate-query` and tested all four held-out positions in every materialized lesson.

Measured scope: 100 lessons per band; 300 lessons; 1,200 exact unique inputs; 1,200 rotations; one declared rival. This is strong finite evidence but not a proof of universal induction, semantic equivalence between grids, all seeds, or undeclared rivals.

## D11 — Add a matched-input gallery-order family without changing production

**Choice.** The task-local native family now has two settings over the same visible inputs: `spatial`, which is the byte-exact selected canonical program, and `largest_overlap_first`. The alternate first computes each frame-local red/blue bounding-box overlap, selects the unique largest overlap, and then cyclically rotates the later packed gallery so that selected frame is first while preserving the remaining spatial order.

**Sequential dependency.** Stage A returns the ordered overlap records and the input-derived largest-frame index. Stage B cannot choose its gallery start until that index exists; it then packs and vertically centers the rotated records. The protected-Racket witness substitutes the canonical spatial start for the selected largest index and changes 58 padded output cells.

**Teaching repair.** An initial held-out query accidentally put the largest overlap first already, so both settings produced the same answer. That profile was replaced rather than weakening the disagreement requirement. The first two demonstrations place the largest overlap at different nonzero indices and refute fixed-start, smallest/widest/tallest, area-sort, key-sort, and top-alignment rivals.

**Evidence.** Final bounded audit: 18 setting/demo jobs, 60 visible pairs, 60 protected-Racket labels, 528 declared-rival checks, 24 public projections, 12/12 held-out setting disagreements, and three substantive 30x30 query banks. Native qualification passed all four setting/seed jobs for seeds 0 and 17; 16 one-query public views and the standardized causal witness replay passed. Copied-runtime task tests passed 35/35.

**Limits.** This is finite evidence over the declared grammar and named rivals, not a universal uniqueness proof. The production `generator.py`, canonical authority, and training state remain unchanged; exact-source owner acceptance is still required.
