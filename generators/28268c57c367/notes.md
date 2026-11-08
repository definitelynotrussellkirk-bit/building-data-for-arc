# Working notes — v2.1.0 repair

Review assignment: review-260b679b826b01a2. Authority b4fa0726be56 unchanged.

The earlier unverified review-2039f1d410b22dbf:v0001 was used as a gray-support lead, not as adopted code or freshly measured evidence. Baseline 300-draw checks found neither off-wall gray nor shared-source rows; final natural seed 6/index 0/medium supplies both plus a right distractor.

A two-profile schedule was chosen instead of independent witness injection or one-rich-per-four: three consecutive demonstrations teach all four declared rivals, and holding out any one of four consecutive draws retains rich. Phase is seed-hashed; using seed+index aliased the shared diagonal probe. Difficulty weighting operates on core too. Natural core has two or three sources; rich has variable source spacing, counts, colors, wall/size and distractors. One designated rich row and a sterile gray row remain intentional support restrictions, not universal task geometry.

The authority's first-source ownership matters: input row 30056050 (wall column 6) yields 33356350, not nearest-source 33356650. The isolated gray does not stop filling, and the later source 6 is retained. CANONICAL_SHORTCUTS lists only rivals fitting all four canonical pairs; gray-as-source fits only the three demonstrations and belongs in LESSON_COMPETITORS instead.

Sampler bounds and strict profile are separate from broader lawful self_check. Pins reconstruct from pixels and never silently clip or drop requested features; obsolete palette/texture/position/density aliases now fail. n_distinct_colors is source-palette size, not total grid palette. Explicit controls may erase teaching witnesses; default lesson guarantees must not be transferred to arbitrary pinned or filtered lessons.

Review measurements and exact commands are retained in the source-bound return, not duplicated into this task indefinitely. Final production census: 300 lessons/1,200 unique inputs, no declared-rival ambiguity in 1,200 rotations. Supplemental probe: 3,024 boundary draws, 480 rotated views, 300 Racket-labeled pairs/211 unique inputs. No hidden solve score or universal induction claim is made. Training approval was not changed.
## Current reviewer considerations

Source SHA-256: `1056cfd90a2ea89d4e95e34ffe4b9f43b922e0590fccdc03ac45414961785241`.

# Distribution decisions — 28268c57c367, v2.1.0

Final source: `1056cfd90a2ea89d4e95e34ffe4b9f43b922e0590fccdc03ac45414961785241`. Authority `b4fa0726be56` unchanged. IDs R1–R3 refer to REVIEW.md; shared follow-ups F1–F3 are in FEEDBACK_TO_CODEX.md.

## Preserve authority, widen inputs (R1)

The original comment explains narrowing to canonical-like sizes and avoiding row interactions; a principled reason to exclude off-wall gray or occupied ray crossings was not recorded. I kept the Racket rule rather than changing labels to match a familiar nearest-source interpretation. All four canonical pairs match both the authority and the independent prefix characterization. The gray-as-source rival fits three canonical demonstrations but fails the labeled canonical test, so it is a lesson competitor but deliberately **not** advertised as fitting every canonical pair. Nearest-source, stop-at-gray and overwrite-obstacles fit all four and are the actual CANONICAL_SHORTCUTS declarations.

## Two-profile, three-demo curriculum (R1)

Independent random witness injection leaves a nonzero chance that every demonstration omits the distinguishing feature; a three-core/one-rich cycle loses its only witness if that rich pair becomes the query. I chose alternating core/rich profiles with a stable, seed-hashed phase. Every consecutive three demonstration draws contain rich, and any four consecutive draws contain two rich; holding out any one leaves a rich demonstration. This is a structural guarantee against the four declared rivals on **unrestricted default** draws, not arbitrary rules.

Production and supplemental tests use the assembly they claim: same seed, same band, consecutive indices, three demonstrations and one query. The production census retains actual materialization/rejection records. The period proof does not survive arbitrary skips, independently reseeded pairs, selection from a mixed pool, shortened lessons, or overrides such as n_gray=0 / one source color that erase witnesses. Such downstream assembly needs a new post-assembly semantic check; two inference guesses do not repair an under-taught lesson.

Intermediate `(seed + index) % 2` was rejected after shared sampling with seed=index selected core only. The final seed-hashed phase avoids that accidental probe alias; difficulty-weighted core heights also make the band effect observable on both profiles. Evidence: failed `checks/after/...defect_lint.log`, `checks/logs/red-breadth.log`, final battery and cyclic probe.

## Geometry and canonical support (R2/R3)

Exact generation axes are height 5..14, width 7..18 and wall 5..16 with wall <= width-2. A minimum five-column left region gives room for two sources, an intervening gray obstacle and a downstream blank; at least one right column permits a distractor. These are **sampler support limits**, not claims about the maximal Racket domain. The validator intentionally recognizes a broader rectangular 1..30 rule domain with a unique full-height wall and an active left source; it rejects malformed grids safely.

Core uses heights 6..9, width height+3 and wall width-3; easy weights smaller heights, hard larger ones, without eliminating canonical-size support in any band. Core has two or three distinct-colored sources on distinct rows, optional isolated gray and empty right side. The original three-source-only repair excluded the two-source canonical test profile, so a failing regression drove the two-source extension. Rich sizes and wall location vary independently within the lawful bounds. The final exact size/palette floor is 6/20, 2/20, 3/20 across bands; the semantic strict profile is 298/600. Reject the alternative of satisfying only marginal dimension envelopes while omitting joint canonical profiles.

## Sources, colors and witness layout (R1/R3)

n_cells=1..6 counts left active sources, and n_distinct_colors=1..6 counts their distinct colors, not the wall or global palette. Natural core is 2..3; natural rich is 2..6 with at least two source colors. All nonzero colors except 5, including formerly absent 1, are eligible. Colors are assigned without dropping requested distinct colors. Natural rich places two different colors in one row, preserves gray between them and a blank after the second, and leaves a separate row available for a gray-not-source witness. The initial fixed two-column source spacing was unnecessary; final spacing and absolute positions vary. Additional sources can share rows and have repeat colors.

The explicit constructor was preferred to unbounded rejection sampling or adding output-conditioned examples: exact controls remain observable, labels stay outside generate(), and capacity at the smallest legal joint settings is tested. Limitation: a forced sterile row and a designated rich source pair are still distribution restrictions, stated rather than hidden.

## Gray and right distractors (R1)

n_gray=0..3 is off-wall gray left of the wall; n_right=0..3 is colored material right of it. Natural rich has two or three gray cells: at least one blocks neither ownership nor continuation, and at least one is isolated on a non-source row with a blank to its right. Natural core may include one isolated gray as in the canonical test. Right distractors use the source palette and must be copied unchanged; they are not treated as invalid merely because the original generator excluded them. Baseline measurement: 0/300 off-wall-gray and 0/300 shared-source-row inputs; final natural seed 6/index 0/medium supplies a Racket-verified 5x8 witness with a right distractor.

## Honest exact controls, no dead aliases (R2)

I retired palette_kind, palette_size, position_bias, density and texture rather than keeping silently ignored controls. This is an intentional version-2 interface change: callers using those names receive ValueError, not pretend compliance. Unknown keys, bool-as-int, floats, strings and out-of-range pins fail loudly. None retains default semantics. Difficulty cannot weaken a pin. Unspecified companion axes adapt, so a single color-count or wall-position pin remains feasible. Only two families of **specific value-pair** contradictions are declared: colors>sources and wall>width-2; there is no blanket multi-axis exemption.

Every exact value is reconstructed from returned pixels by observe_overrides(). The shared final matrix has 114,210 draws, 0 findings/warnings, and 7,290 expected incompatible rejections; the additional 504-setting joint-boundary product runs both profile positions in all bands (3,024 accepted draws). These counts are draw counts, not unique inputs. Ordinary gray/right distractors were preferred to preserving fake 'degenerate texture' modes that mixed malformed inputs with useful cases.

## Rejected proposals and residual risk

Changing the Racket authority to nearest-source semantics was rejected: it would erase precisely the legal branch needing instruction. Independent Bernoulli witness sampling, a single-rich/four-pair cycle, fixed source spacing, three-source-only core and inert difficulty labels were rejected as above. Expanding to every lawful tiny canvas, allowing entirely blank/identity lessons by default, or adding unrelated shape families was deferred to avoid conflating task-domain validity, useful teaching and output diversity. Controls that deliberately erase witnesses are accepted as input controls, not promised as sufficient teaching lessons.

The selected patch leaves training approval unchanged. No broad learning benefit or hidden-query score was measured. The final production census, required-rotation run and cyclic probe rule out only the named rivals on their recorded populations; counts from overlapping windows are never presented as independent examples.
