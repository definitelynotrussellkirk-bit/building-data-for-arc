# Review notes: 5a6a772cd217

## Baseline finding

The selected `2.1.0` sampler had no pinned `RULE_HASH`, advertised mostly dead or inexact axes, silently accepted unknown/typo overrides, used a weak validator, and declared no executable semantic contract. Its random placement taught a physical left-to-right shortcut even though the authority orders frames by top row then left column. The hard-band profile floor also had no exact canonical-profile hit.

No prior associated note or prior return was available as a lead: `evidence/associated_notes.jsonl` was empty. The review therefore used the frozen selected baseline, canonical examples, and unchanged Racket authority directly.

## Repair

- Replaced fake scalar controls with exact `canvas_profile` and `density` controls recoverable from pixels.
- Added six deterministic canvas profiles: all four canonical height/width/palette profiles and two broader profiles.
- Added rejection-free placement for two or three exact hollow frames.
- Alternated row-major-vs-physical-order conflict lessons with canonical-order lessons.
- Preserved full interiors, including zero rows/columns, and forced examples that expose both asymmetric narrow-panel padding branches.
- Added a complete structural parser/validator, exact override observer, independent Python rule mirror, five executable rivals, five witnesses, and a three-demo lesson-identifiability hook.
- Added portable task-local regression tests under `tests/`.
- Left the canonical Racket authority unchanged and pinned `RULE_HASH = "64fd3246321b"`.

## Final evidence

Final generator SHA-256: `c228465d1d7f6944b8e65ca84ae3c523a02edb9194b4341c85980cf44883a4d0`.

- Full after battery: 12/12 stages green, no advisories or failures (`checks/after-3/`).
- Focused suite: 10/10 passed (`checks/focused-tests-green-4.log`).
- Portable task tests: 10/10 passed (`checks/task-tests-3/result.json`).
- Semantic gate: 600/600 strict draws, 5/5 witnesses, 12/12 ordered lessons, 0/48 ambiguous rotations (`checks/semantic-3/`).
- Wide census: 300/300 lessons, 1,200 unique inputs, 0 production ambiguities, 0/1,200 ambiguous rotations (`checks/lesson-census-{easy,medium,hard}.json`).

## Limits

The identifiability claim is finite: it covers the declared rivals, not every possible program. The emitted domain intentionally stays at two or three frames, six canvas profiles, one non-gray interior color per frame, and three density levels. The census covers 100 lessons per band and every pair holdout within those lessons, not all seeds or every conceivable schedule.
## Current reviewer considerations

Source SHA-256: `c228465d1d7f6944b8e65ca84ae3c523a02edb9194b4341c85980cf44883a4d0`.

# Decisions for `5a6a772cd217`

The original task notes were empty, so original intent is marked **unknown** where it was not explicit in source. Inferences from the baseline are labeled as such. All final measurements are bound to generator SHA-256 `c228465d1d7f6944b8e65ca84ae3c523a02edb9194b4341c85980cf44883a4d0`.

## D1 — Keep the Racket authority unchanged

- **Original rationale:** unknown; the imported authority was already canonical and executable.
- **Choice:** pin `RULE_HASH = "64fd3246321b"` and treat Racket as the only output authority.
- **Alternatives considered:** rewrite the authority to match the old summary's left-to-right description; normalize away the asymmetric padding.
- **Probe:** canonical rule smoke, Racket lint, and authority-sync stages all passed before and after; the Python mirror agrees on canonical pairs and generated support.
- **Failure mode avoided:** silently changing the task to fit an inaccurate sampler description.
- **Limit:** the Python mirror is test support, not a second authority.

## D2 — Replace fake scalar axes with two exact categorical axes

- **Original rationale:** inferred from baseline comments: many axes were copied from a generic template, but most did not affect pixels or were silently ignored.
- **Choice:** advertise only `canvas_profile` and `density`; reject every unknown override.
- **Alternatives considered:** retain `grid_h`, `grid_w`, frame count, palette size, and layout as independent axes; declare many incompatibility combinations.
- **Probe:** all 18 profile/density combinations were exercised in every band; `observe_overrides` recovered requested values exactly and typo overrides failed.
- **Failure mode avoided:** metadata claiming independent controls that geometry later clips, ignores, or cannot realize.
- **Limit:** callers cannot request arbitrary dimensions; they select one of six lawful profiles.

## D3 — Use six uniquely observable canvas profiles

- **Original rationale:** baseline sampled a narrow 8–10 by 14–18 range with two frames, apparently to resemble canonical examples.
- **Choice:** four profiles exactly cover the canonical `(height, width, foreground-palette-size)` support—`8×14/2`, `9×15/2`, `8×16/2`, `9×17/3`—and two broaden it to `10×18/3` and `10×20/2`.
- **Alternatives considered:** only canonical profiles; a much wider random canvas range.
- **Probe:** profile-floor and override stages passed in all bands; shapes uniquely map back to profile names.
- **Failure mode avoided:** hard-band zero canonical-profile hits and ambiguous override observation.
- **Limit:** geometric support is intentionally finite rather than exhaustive.

## D4 — Generate exact hollow frames with rejection-free placement

- **Original rationale:** baseline intended nonoverlapping hollow gray frames but used a 40-attempt random placement loop that could return fewer than requested.
- **Choice:** construct frame boxes analytically with exactly one zero column between physical neighbors and seeded whole-block translation.
- **Alternatives considered:** keep rejection sampling with a fallback; allow overlapping/touching frame components.
- **Probe:** structural parser accepted all sampled/canonical inputs and rejected corrupt walls, stray colors, touching frames, and malformed interiors.
- **Failure mode avoided:** silent underproduction, merged components, or partial frames.
- **Limit:** generated frames are 4–5 rows by 3–5 columns and do not cover every rectangle size the abstract rule could process.

## D5 — Teach two and three frames, with distinct interior colors

- **Original rationale:** baseline fixed two frames and two distinct colors; canonical support includes a three-frame example.
- **Choice:** profile controls determine exactly two or three frames, each with one pairwise-distinct color from `{1,2,3,4,6,7,8,9}`.
- **Alternatives considered:** always two frames; repeated interior colors; arbitrary extra nonzero distractors.
- **Probe:** canonical-profile floor, strict validator, and all six profile overrides passed.
- **Failure mode avoided:** a learner equating the task with exactly two panels or using color identity to pair/order frames.
- **Limit:** no repeated-color frames or unrelated distractor objects are generated.

## D6 — Alternate row-order conflict and canonical-order layouts

- **Original rationale:** baseline summary said left-to-right, but the authority sorts by top row then left column; random placement did not guarantee a contradiction.
- **Choice:** `sample_index % 2` alternates `row_order_conflict` and `canonical_order`. In the conflict profile the topmost frame is physically rightmost.
- **Alternatives considered:** only conflict layouts; purely random layouts and hope a conflict appears; change the authority to left-to-right.
- **Probe:** `row_major_not_left_to_right` fired 278/600 strict draws across all bands; the declared `left_to_right` rival disagreed on all 60 independently checked witness cases.
- **Failure mode avoided:** perfectly correct labels that nevertheless teach the wrong ordering shortcut.
- **Limit:** this is one controlled conflict family, not every possible spatial permutation.

## D7 — Preserve full interiors and make density exact

- **Original rationale:** baseline painted a random sparse subset inside each frame, but no exact density contract existed.
- **Choice:** `sparse`, `balanced`, and `dense` produce exact colored-cell counts while retaining at least one zero cell. The 5×5 frame leaves a leading blank row/column so tight-crop behavior is observably wrong.
- **Alternatives considered:** random percentage density; fully filled interiors; use a separate texture axis.
- **Probe:** all density overrides were exact; the full-interior witness fired 600/600 and refuted `tight_crop_interiors` on 60/60 checked cases.
- **Failure mode avoided:** a learner cropping to colored pixels rather than extracting the frame-defined interior.
- **Limit:** one color per interior and three occupancy levels simplify the domain.

## D8 — Expose both asymmetric narrow-panel padding branches

- **Original rationale:** absent from the old summary; discovered by reading and testing the selected authority.
- **Choice:** every shape schedule includes narrow panels, and the unique wide panel changes row-major position across profiles. The first narrow panel receives trailing zero padding; later narrow panels receive leading zero padding.
- **Alternatives considered:** make every interior at least three columns; normalize all padding to one side.
- **Probe:** first-panel and later-panel witnesses fired in all bands; `always_leading_narrow_pad`, `always_trailing_narrow_pad`, and `raw_concat` were independently refuted.
- **Failure mode avoided:** labels that fail to reveal an authority branch responsible for different outputs.
- **Limit:** the generator targets widths one through three after extraction, not arbitrarily wide panels.

## D9 — Require three demonstrations and rotation-safe lessons

- **Original rationale:** unknown; shared materialization defaults to three demonstrations and one query.
- **Choice:** declare `EXAMPLES_NEEDED = 3`, executable lesson rivals, and a deterministic two-profile schedule whose every 3-of-4 holdout still eliminates all rivals.
- **Alternatives considered:** rely on two inference guesses; require only the production query position; use more demos.
- **Probe:** semantic smoke 12/12 production lessons and 0/48 ambiguous rotations; wide census 300/300 production lessons and 0/1,200 ambiguous rotations.
- **Failure mode avoided:** a lesson that is valid only because one critical witness happens to remain in the demonstrations.
- **Limit:** rotation safety is proven only for declared rivals over the sampled lessons, not all hypotheses or all seeds.

## D10 — Add a full parser, mirror, rivals, and portable tests

- **Original rationale:** baseline `self_check` only checked for frame-colored cells and no task-local tests existed.
- **Choice:** one structural parser powers validation and override observation; independent output functions represent the authority and five plausible wrong rules. Tests locate packet roots through `reviewer_support` rather than fixed parent depth.
- **Alternatives considered:** ad hoc assertions per test; compare only saved outputs; fixed-path imports.
- **Probe:** focused suite and portable staged suite each passed 10/10; corruption tests fail for the intended reason.
- **Failure mode avoided:** green tests that merely restate implementation details or break when copied into the staged runtime.
- **Limit:** parser and mirror still need maintenance if the canonical authority changes in a future version.

## Difficulty policy

Difficulty changes the starting offset through the six-profile cycle; it does not change the rule or invalidate any override. This avoids the intermediate defect where easy, medium, and hard defaults were byte-identical while keeping every exact profile/density combination legal in every band. Across eighteen consecutive sample indices each profile/density pair appears exactly once per band.
