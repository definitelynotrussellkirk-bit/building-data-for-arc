# Working notes: 504e304a77f1

## Current rule and source identity

Version `3.0.1`; generator SHA-256 `59e9cb73c92dd439a0073d7447b4dc5df143be392f04ec00d2e98785538c3b9b`; canonical `RULE_HASH = 6c92d838a5dd`.

The input contains 2–4 same-colour hollow rectangular frames and the same number of ordinary, differently coloured components on background 0. Sort ordinary components by **cell count**, sort frames by **interior area**, erase the original components, and center each cropped component inside the frame of matching rank. Same-colour 4-connectivity is used so the canonical task's disconnected common-colour frames remain separate components.

## Root cause found in the selected 2.1.0 baseline

The prior generator expressed a materially different visual language: large independently coloured frames, a large random scatter canvas, and a retry/fallback path that frequently collapsed difficult samples to a single frame plus domino. Its validator grouped every cell of a colour together, so it rejected all canonical examples whose common-colour frames were disconnected. Several declared axes were dead or only weakly observable. The canonical demonstrations also left the plausible “rank movers by bounding-box area” rule observationally equivalent to the intended cell-count ranking.

The original rationale for those choices is unknown. `workspace/generator_v2_1_before.py` preserves the selected pre-repair implementation; `checks/before/` and the interrupted follow-on before runs preserve measured failures.

## Decisions and reversals

1. **Reversed distinct frame colours to one shared frame colour.** This restores the canonical object language and deliberately tests component separation rather than colour-as-identity.
2. **Reversed retry/fallback sampling to constructive placement.** Every legal axis combination is built directly; generation either returns the requested contract exactly or raises. There is no silent simplification path.
3. **Replaced broad-only scatter with two strata.** Every fifth default sample is a 6×21 canonical-profile gallery with frame colour 5, three pairs, and the canonical 1/3/4 cell-count ladder. The other four samples use broader 2–4-pair gallery/scattered layouts.
4. **Added a cell-count versus bbox-area teaching witness.** Broad samples use shapes with cell counts 5,6,8,9 but bbox areas 9,6,8,10. `counterexamples/bbox_area_rank.json` retains a minimal lawful disagreement and the focused test suite covers it.
5. **Reduced the public exact axes to four real controls:** `n_pairs`, `layout`, `frame_color`, and `bbox_rank_inversion`. Unknown keys, invalid types, and out-of-domain values are rejected before generation. `observe_overrides` reconstructs every requested value from pixels.
6. **Compressed broad canvases after an intermediate failure.** The first constructive rewrite had median area 600 versus canonical 126. A failing regression test was added before reducing gallery/scattered canvases to 12×30 and 16×28; the final strict defect lint passes.
7. **Left the Racket authority unchanged.** Rule smoke, Racket lint, and authority sync all pass against the pinned canonical rule.

## Lesson policy and evidence

`EXAMPLES_NEEDED = 2`. The production sampler materializes two demonstrations and one query from contiguous sample indices. Core samples occur every fifth index, so any two examples in a three-pair window contain at least one broad bbox-rank inversion. The declared semantic witness, rival, canonical shortcut, and lesson competitor are all `bbox_area_rank`-linked.

Final source-bound evidence:

- Full battery: `checks/after-v3.0.1/checks/504e304a77f1_after_battery_summary.json` — 12/12 stages green.
- Semantic battery: 600 draws, strict rate 1.0, bbox-rank witness in 485/600 draws, 12/12 production lessons identifiable, 36/36 rotations identifiable.
- Large census: `checks/lesson-census-final.json` — 300/300 production lessons and 900/900 query rotations identifiable, 0 ambiguity/errors, 890 unique inputs.
- Post-repair visible-only solve: first general implementation passed 3/3 visible examples; masked query correctness remains unknown.

## Known limits and open findings

The generator samples a finite family of shape templates, 2–4 pairs, one shared frame colour, and two layout families; it does not claim exhaustive coverage of all lawful ARC instances. Semantic evidence is finite and checks the declared bbox-area competitor, not every imaginable rival rule. The deterministic core/broad period is intentional curriculum structure and may be unsuitable if a downstream sampler does not preserve the documented contiguous-window policy. No blocking defect remains in the measured final source.
## Current reviewer considerations

Source SHA-256: `59e9cb73c92dd439a0073d7447b4dc5df143be392f04ec00d2e98785538c3b9b`.

# Decisions for 504e304a77f1

## D1 — Use same-colour 4-connected components

**Choice.** Frames and movers are decomposed by colour and 4-connectivity; a hollow rectangular component is a frame and every other component is a mover.

**Why.** Canonical frames all use the same colour but are spatially disconnected. The old implementation grouped an entire colour globally and therefore rejected the real task. Four-connectivity matches the canonical frame/object geometry and the selected rule's component semantics.

**Alternatives rejected.** Global colour grouping was disproved by canonical examples. Colour-agnostic connectivity would merge adjacent differently coloured cells and would not preserve object identity. Eight-connectivity would introduce diagonal merges not required by this task.

**Probe.** Every canonical input is accepted by `self_check`, and the Python mirror reproduces every canonical output. Focused tests cover both claims.

**Failure mode / limit.** This choice excludes diagonal-only same-colour components. That is deliberate for the documented domain, not a universal ARC convention.

## D2 — Combine a canonical core with a broader curriculum

**Choice.** Every fifth default draw is a strict 6×21, three-pair gallery with frame colour 5 and the canonical 1/3/4 mover-size ladder. Other draws use 2–4 pairs in gallery or scattered layouts.

**Why.** A broad-only generator had zero canonical-profile support and taught the wrong visual language. A canonical-only clone would have low diversity and would preserve the bbox-area shortcut. The split makes canonical recognition frequent while reserving most samples for disambiguating variation.

**Alternatives rejected.** Randomly hoping to hit canonical dimensions was too weak and failed the profile gate. Making every sample canonical would not teach the disputed ranking statistic. A hidden fallback was rejected because it silently changes requested difficulty and axes.

**Probe.** The strict profile gate reports support in every band. The 600-draw semantic census measured 115 core and 485 broad profiles; both are accepted by the same validator.

**Failure mode / limit.** The period-five schedule is deterministic. Downstream assemblers should use the documented contiguous production policy or rerun identifiability checks for a different policy.

## D3 — Use one shared frame colour

**Choice.** All frames in a puzzle share one nonzero colour; every mover has a distinct nonzero colour different from the frame colour.

**Why.** This matches the canonical task and forces the solver to separate frames by connectivity and geometry rather than assigning each frame by a unique colour.

**Alternatives rejected.** Distinct frame colours were easier to parse but materially changed the problem and allowed colour identity to replace component reasoning.

**Probe.** Canonical examples and all generated samples pass the shared-colour invariant. `observe_overrides` recovers the frame colour exactly.

**Failure mode / limit.** The generator does not cover lawful variants with mixed frame colours because those are outside the selected canonical language.

## D4 — Construct every legal sample; never retry into a fallback

**Choice.** Gallery and scattered layouts use predetermined collision-free regions sized for all supported shape/frame combinations. Generation validates the result and raises on an internal contradiction.

**Why.** The previous retry/fallback path made distribution claims unreliable: hard requests could return a trivial one-pair example. Constructive placement makes the requested axes the returned axes.

**Alternatives rejected.** Unbounded/random rejection sampling is harder to audit and can bias distributions. A “best effort” fallback masks defects.

**Probe.** All Cartesian combinations of `n_pairs`, `layout`, `frame_color`, and `bbox_rank_inversion` are covered by focused parameterized tests. The strict override gate passes with unknown-key rejection.

**Failure mode / limit.** Constructive regions constrain the family of spatial arrangements. Broader layout families would need explicit new constructors and tests.

## D5 — Make bbox-area ranking a named competitor

**Choice.** Broad samples use a shape ladder with cell counts `5,6,8,9` and bbox areas `9,6,8,10`, creating a rank inversion. The generator declares the same implementation under `SEMANTIC_RIVALS`, `CANONICAL_SHORTCUTS`, and `LESSON_COMPETITORS` and links it to a witness.

**Why.** All canonical pairs fit both cell-count and bbox-area ranking, so correct labels alone do not teach which statistic is intended. A generated disagreement is necessary training evidence.

**Alternatives rejected.** Merely documenting the intended rule does not change the data. Random polyominoes might occasionally separate the rules but offer no lesson-level guarantee.

**Probe.** `counterexamples/bbox_area_rank.json` is a lawful retained disagreement. The semantic battery found witness support in 485/600 draws and confirmed 60/60 sampled witness/rival disagreements. The 300-lesson census found no surviving rival in production or any query rotation.

**Failure mode / limit.** This names one high-value rival, not every possible alternative ranking rule.

## D6 — Keep only four exact, pixel-observable controls

**Choice.** Public axes are `n_pairs`, `layout`, `frame_color`, and `bbox_rank_inversion`; each is strictly typed, range checked, and reconstructible from the returned grid.

**Why.** The selected baseline advertised controls whose effect was absent or weak. Exact controls are useful only when a caller can trust that they were honored.

**Alternatives rejected.** Keeping decorative metadata axes would inflate apparent diversity without changing the data. Silent acceptance of unknown keys was rejected because misspellings become invisible distribution bugs.

**Probe.** Parameterized tests cover every legal combination across difficulty values, invalid values, bad types, and unknown keys. The final override stage is green.

**Failure mode / limit.** Shape orientation and object colours remain deterministic keyed draws rather than caller-controlled axes; that keeps the contract small and avoids controls that are difficult to observe unambiguously.

## D7 — Compress broad canvases after measured area drift

**Choice.** Broad gallery and scattered canvases are 12×30 and 16×28 rather than the initial 20×30-scale rewrite.

**Why.** The first constructive version passed semantic checks but strict defect lint measured median area 600 versus canonical 126. This was an unintended distribution shift, not useful difficulty.

**Alternatives rejected.** Waiving the defect warning would retain a visual shortcut based on excessive blank space. Shrinking all samples to 6×21 would reduce layout diversity.

**Probe.** A regression test first reproduced the failed area guard, then passed after compression. Final strict defect lint is green.

**Failure mode / limit.** Broad samples are still larger than canonical; this is intentional but bounded.

## D8 — Leave the Racket authority unchanged

**Choice.** No canonical or archival Racket source was edited.

**Why.** The rule smoke already showed the authority implements the intended transform. The defects were in sampling, validation, controls, and teaching support.

**Alternatives rejected.** Editing a correct authority would add risk without addressing the data distribution.

**Probe.** Final rule smoke, Racket lint, and authority sync all pass; `RULE_HASH` is pinned to `6c92d838a5dd`.

## D9 — Require two demonstrations and test all query rotations

**Choice.** `EXAMPLES_NEEDED = 2`; production lessons use two contiguous demonstrations plus one query. A core sample appears only every fifth index, so every two-of-three rotation includes at least one broad inversion case.

**Why.** One example can be accidentally compatible with the bbox rival. Two demonstrations are sufficient under this deterministic schedule while keeping lessons compact.

**Alternatives rejected.** One demonstration was underdetermined. Three or more demonstrations add cost without improving the measured declared-rival result for this schedule.

**Probe.** Semantic smoke: 12/12 production lessons and 36/36 rotations. Large census: 300/300 production lessons and 900/900 rotations, 0 ambiguities.

**Failure mode / limit.** A different sampler that selects noncontiguous examples could violate the schedule argument and must rerun the census.
