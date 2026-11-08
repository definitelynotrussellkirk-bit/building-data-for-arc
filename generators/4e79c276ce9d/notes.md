# Current generator notes: 4e79c276ce9d

## Intended rule and authority

Find monochrome nonzero components using four-neighbor connectivity. Select the component with the fewest occupied cells; the selected Racket authority breaks a size tie by top row and then left column. Return only that component, translated to the origin inside its exact bounding box, preserving zeros in sparse shapes.

`RULE_HASH = 5d74c60efd43` is pinned. The canonical Racket program was not changed. The selected base record's `target_code` previously differed from `raw_code` only by comments; this review synchronized the active text exactly. Execution behavior and the rule hash did not change.

## Baseline decision reversed

The inherited 3.0.1 generator exposed five dead, aliased, or silently swallowed controls; omitted a rule pin and keyed default-axis provenance; never reached the canonical five-color profiles; had no executable lesson/rival contract; and permitted canonical-fitting shortcuts such as “choose the smallest bounding box.” The baseline battery finished with five failing stages and two advisories. No prior return was used as a repair lead; the current selected baseline, canonical pairs, battery evidence, and direct Racket executions were used.

Version 4.0.0 replaces that design rather than extending its random-polyomino controls. The public exact control surface is intentionally only:

- `grid_h`: literal integer 9–12
- `grid_w`: literal integer 10–13

Unknown keys, Booleans, nonintegers, and out-of-range values reject. Both scheduled defaults and explicit controls are recorded through `GenCtx`, and `observe_overrides` reports the realized dimensions.

## Distribution and curriculum

The default six-position schedule is:

1. canonical-profile scene, 11×11, five colors including background;
2. rich L-shaped witness, 10×12, four colors;
3. rich Z-shaped witness, 12×10, four colors;
4. canonical-profile scene, 10×10, five colors;
5. rich L-shaped witness, 9×13, four colors;
6. rich Z-shaped witness, 10×12, four colors.

Lessons use three demonstrations plus one query. Every cyclic four-pair window and every held-out query position leaves at least one rich demonstration. Canonical-profile scenes use four distinct colors and object sizes 2, 3, 4, and 5. Rich scenes use component sizes 5, 6, 7, and 8 and deliberately arrange:

- a sparse five-cell target whose bounding box is larger than the compact six-cell distractor;
- a same-color seven-cell component touching the target only diagonally;
- a different-color compact component touching that cluster by an edge;
- a non-target component earlier in reading order;
- a sparse target whose exact crop differs from a solid bounding box.

The declared rivals are `bbox_area`, `solid_bbox`, `multicolor_connectivity`, `eight_connectivity`, `rare_color`, `color_partition`, and `top_left`. The first six fit every usable canonical pair; rich scheduled inputs refute all seven.

## Retained evidence

- Strongest canonical-fitting shortcut and Racket-labeled generated witness: `counterexamples/bbox_area_rival.json`.
- Reusable source-bound probe: `workspace/probe_smallest_object.py`.
- Final battery: all 12 stages green with required rotations.
- Focused task tests: 18 passed after adding the tool and retained counterexample.
- Independent Python/Racket comparison: 35/35 matched.
- Large lesson census: 300/300 materialized lessons, 1,200 pairs and 1,200 held-out rotations, zero ambiguity, hook warnings, or scoring errors against the seven declared rivals.
- Exact schedule census: 18/18 starts and 72/72 query rotations at seed 441 across easy, medium, and hard, zero ambiguity.

## Limits and open questions

The evidence is finite and only excludes declared rivals; it does not prove unique induction against every possible conditional or template-memorization rule. Rich scenes use two base shape families under a restricted set of dihedral transforms, so downstream expansion could add more source shapes while preserving the same counterexample relations. Explicit dimension overrides preserve the task law but are not promised to retain an exact canonical size profile. Passing checks do not itself change catalog approval or training safety.
## Current reviewer considerations

Source SHA-256: `c0a660b4ab4b53fb8c3d6c5f1709e62af833f12baddd403b355d7721242c4967`.

# Decisions for 4e79c276ce9d

## D1 — Preserve the selected rule; synchronize only active text

**Inherited choice:** the selected Racket authority already implemented the canonical rule, but the base record's active `target_code` differed from `raw_code` by comments.

**Decision:** leave the executable rule and canonical data unchanged; replace only the stale active text with the exact selected `raw_code`. Pin `RULE_HASH = "5d74c60efd43"` in the generator.

**Why:** canonical execution was correct. Changing the law would add risk without addressing the generator defects. The final authority-sync and rule-smoke stages pass, and 35 independent Python/Racket comparisons agree.

**Alternative rejected:** editing the Racket program to match an easier generator. That would reverse the source of truth and was not justified.

## D2 — Replace the inherited control surface instead of preserving dead knobs

**Inherited choice:** several palette, texture, color-count, shape, and layout controls were advertised, aliased, inert, or silently swallowed. Scheduled defaults also lacked exact draw provenance.

**Decision:** expose only two exact controls that are both useful and directly observable from a returned grid: `grid_h` 9–12 and `grid_w` 10–13. Unknown keys, Booleans, nonintegers, and out-of-range values fail closed. Both scheduled values and overrides pass through keyed `GenCtx` draws.

**Why:** a small truthful API is better training and tooling data than a large nominal one. The final override stage passes, and the task probe covers all 48 band/joint-dimension combinations.

**Failed intermediate:** the first replacement returned scheduled dimensions directly rather than recording keyed draws. The override checker found 120 missing-provenance rows. A new test first reproduced the `KeyError`, then the default path was changed to fixed-bound keyed draws.

**Alternative rejected:** retaining a `texture` alias for compatibility. It would recreate the exact ambiguity the battery was designed to detect.

## D3 — Make every default draw match an exact canonical profile

**Decision:** use a six-position schedule whose default `(height, width, palette-size)` tuples are drawn only from the five canonical profiles. Two positions use four distinct foreground colors plus background; four rich positions use three foreground colors plus background.

**Why:** the inherited generator could not reach canonical five-color inputs. Exact profile support reduces distribution shift while still allowing adversarial teaching scenes. In 300 final probe draws, all 300 matched a canonical profile; every profile appeared, with counts retained in `checks/probe-final.json`.

**Alternative rejected:** merely increasing random palette size. That would improve a superficial statistic without guaranteeing recurrence of actual canonical profiles or semantic witnesses.

## D4 — Teach component size with relational counterexamples

**Decision:** construct rich scenes with component sizes 5, 6, 7, and 8. The five-cell target is sparse, while the six-cell distractor is compact. The target color is reused by a diagonally touching seven-cell component, and a different-color compact component edge-touches that cluster. A non-target appears earlier in reading order.

**Why:** one input then refutes seven plausible rules at once: bbox area, solid bbox, multicolor connectivity, eight-connectivity, rare color, whole-color partition, and top-left selection. The strongest canonical-fitting rival is retained as a Racket-labeled counterexample.

**Alternatives rejected:**

- Random independent polyominoes: broad-looking but did not reliably create the required contrasts.
- One witness per rival: larger schedule, more brittle lesson assembly, and unnecessary when a single lawful scene can expose the distinctions jointly.
- Color permutations alone: insufficient for connectivity and bbox-area shortcuts.

## D5 — Use a six-start cyclic curriculum with three demonstrations

**Decision:** declare `EXAMPLES_NEEDED = 3` and `LESSON_SCHEDULE_PERIOD = 6`, with pattern `canonical, rich, rich, canonical, rich, rich`. Check every one of the six starts and all four possible held-out query positions in each band.

**Why:** every three-demo subset of a four-pair window retains at least one rich witness, even under arbitrary query rotation. The exact schedule census materialized 18/18 band/start lessons and 72/72 rotations with zero declared-rival ambiguity. The larger production census materialized 300/300 lessons and 1,200/1,200 rotations, also with zero ambiguity.

**Alternative rejected:** rely on the normal ordered query only. The packet explicitly asks for rotations when claimed; a schedule that teaches only one held-out position would be fragile downstream.

## D6 — Restrict geometric transforms to preserve the reading-order witness

**Initial attempt:** use all eight dihedral transforms.

**Observed failure:** some transforms moved the true target before every distractor, allowing the `top_left` rival to survive a rich input. The focused regression caught this before the full battery.

**Decision:** use the four transform codes that still vary orientation while preserving a non-target earlier in scan order.

**Why:** transform variety is useful only if it does not erase the teaching relation. All rich draws in the probe now refute `top_left` as well as the other six rivals.

**Limit:** this narrows geometric variety. Future expansion can add new base layouts designed to preserve the same relation under additional transforms.

## D7 — Keep `self_check` broad enough for canonical data

**Decision:** validate the task law rather than just the generator template: rectangular ARC grid, background zero, at least two monochrome four-connected components, unique smallest component, and no foreign color inside the selected component's bbox. Canonical inputs are accepted and matched by the mirror.

**Why:** validators should not reject lawful canonical examples merely because they were not produced by the current constructor.

**Alternative rejected:** require exactly four components or the generated 2/3/4/5 and 5/6/7/8 size patterns. Those are curriculum choices, not rule-domain requirements.

## D8 — Retain source-bound tools and genuine failed iterations

**Decision:** add `workspace/probe_smallest_object.py`, focused tests, and the exact bbox-area counterexample. Preserve the baseline failures, test-first red runs, intermediate lint/provenance battery, blind-solve failed revision, and both audit findings.

**Why:** future agents can rerun the contract without copying declarations, and maintainers can distinguish measured failures from retrospective descriptions.

## D9 — Limit claims to the tested rival set

The final evidence excludes seven declared rivals over the measured source, schedule, and sample ranges. It does **not** prove universal rule identifiability. Fixed object templates, schedule position, or a contrived conditional hypothesis could still be exploited. This limitation is explicit in the generator notes, probe output, and review brief.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-1dd6d761b745997e:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `c0a660b4ab4b53fb8c3d6c5f1709e62af833f12baddd403b355d7721242c4967`. At disposition, audited bytes match the current source.

### Current decision

No issue found within reported 18 task tests, strict defect lint and seven declared rivals on unchanged c0a660b4ab4b source. Finite reviewer audit only; no approval upgrade or clearing other findings.

### Assessment or prior finding

## 4e79c276ce9d

**No issue found in the checked source** (`c0a660b4ab4b53fb8c3d6c5f1709e62af833f12baddd403b355d7721242c4967`).

I checked the rule pin, canonical-pair acceptance, exact dimension controls,
canonical-fitting shortcut declarations, rich witness profiles, and every cyclic
held-out-query rotation covered by the target's source-bound tests. The portable
task-test stage passed **18/18**, and strict defect lint reported **0 findings**.
Evidence: `checks/audit/4e79c276ce9d-task-tests/result.json`,
`checks/audit/4e79c276ce9d-task-tests/checks/task_tests.xml`, and
`checks/audit/4e79c276ce9d-defect-lint/checks/4e79c276ce9d_audit_defect_lint.log`.

This is a finite audit against the target's seven declared rivals and existing
probe coverage; it is not a proof against arbitrary conditional hypotheses. No
files under `generators/4e79c276ce9d/` were changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
