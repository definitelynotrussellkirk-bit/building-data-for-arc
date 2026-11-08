# Current notes: 75be7448827f

## Intended rule and authority

Detect each separate hollow color-1 rectangular frame, count nonzero cells in its interior, choose the first top-left frame attaining the largest raw count, and return that interior crop unchanged. The selected Racket authority was not edited. `RULE_HASH = "6f03f2e69da2"` pins the current canonical source.

## Repaired distribution

Version 2.2.0 constructs two or three nonoverlapping lawful frames and a unique count winner with 6–8 cells and a 1–2-cell margin. Default examples alternate by `sample_index`:

- even indices: the count winner is the largest frame, while a smaller frame is denser;
- odd indices: the count winner is densest, while a larger frame has fewer cells.

Thus any consecutive three demonstrations contain both conflict types and refute the simple `highest_density` and `largest_area` selectors. The public exact axes are `grid_h`, `grid_w`, `n_frames`, `winner_count`, `count_margin`, and `rival_kind`; unknown, mistyped, or out-of-range values reject instead of being ignored.

Every fourth unoverridden sample anchors one of the five canonical `(height, width, palette-size)` profiles in every difficulty band. Other samples retain the broader 13–20 by 14–22 scale, two/three-frame variation, reflections, placement, colors, and cell patterns.

## Decision reversals

- **Original selected baseline:** optimized a unique density winner even though the authority uses raw count. A 4,000-draw probe found 1,140 count ties and 576 unique count/density disagreements with zero `self_check` failures (`checks/before/semantic_probe.json`).
- **Version 2.0/2.1 intermediate:** constructed a unique count winner and a denser loser, but always made the count winner the largest-area frame. Final self-review identified that new shortcut.
- **Version 2.2 current:** alternates density-conflict and area-conflict examples and declares/tests both rivals. TDD evidence is retained in `checks/tdd-red-3/` and `checks/tdd-green-3/`.

## Validation and semantic contract

`self_check` now validates a rectangular 0–9 grid, exact hollow frame components, nonoverlap, one distinct non-frame color per interior, distinct colors across frames, and no stray foreground. `observe_overrides` measures every public axis. `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `lesson_identifiable` cover density and area shortcuts.

## Known limits and open findings

- Generated examples intentionally have a unique count winner; they do not teach the authority's top-left tie break. Canonical pairs still exercise and validate that behavior.
- The lesson guarantee assumes the normal consecutive sample-index assembly with three demonstrations. Forcing the same `rival_kind` override across a whole lesson can remove one counterexample and should be rejected by `lesson_identifiable`.
- Frame shapes remain from the small 3x3, 3x4/4x3, and 4x4 family inside broader canvases. This is adequate for the tested selection rivals but is not exhaustive geometric coverage.
- Finite declared-rival censuses do not prove universal identifiability against every possible hypothesis.
## Current reviewer considerations

Source SHA-256: `010cb74c9da2d7832b302c403f834c84a85746eaf245c65c61bc30d5a28866cb`.

# Decisions for 75be7448827f

Final generator source SHA-256: `010cb74c9da2d7832b302c403f834c84a85746eaf245c65c61bc30d5a28866cb`.

## D1 — Use raw nonzero-cell count, not density

**Original choice.** The selected baseline's prose and sampler targeted the densest frame. The original rationale is unknown; it likely attempted to make a unique visual winner.

**Why reversed.** The canonical Racket authority counts all nonzero interior cells. The source-bound baseline probe made 1,000 calls in each of default/easy/medium/hard: 1,140 calls had raw-count ties and 576 calls had unique count and density winners that differed, while `self_check` rejected none. This is label ambiguity or semantic mismatch hidden by a structure-only validator (`checks/before/semantic_probe.json`).

**Alternatives considered.** Relabeling with the density rule was rejected because the Racket authority and canonical outputs are authoritative. Rejection sampling from the old distribution was rejected because it would leave the wrong design objective and make exact controls unreliable.

**Decision.** Construct a unique raw-count winner directly and keep the Racket rule unchanged.

## D2 — Refute both density and largest-area shortcuts

**First repair choice.** Version 2.0/2.1 used a 4x4 count winner and a 3x3 denser loser. It correctly separated count from density.

**Failure mode found during final self-review.** The winner was always the largest-area frame, so a model could ignore cell counts and choose the largest rectangle. The red regression in `checks/tdd-red-3/` made this failure explicit.

**Alternatives considered.** A single three-frame layout with winner always at the middle area rank would merely replace “largest” with a “middle-size” shortcut. Random unconstrained shapes could reintroduce ties or make rival coverage probabilistic.

**Decision.** Alternate two constructive modes by default sample-index parity:

- `density`: a 4x4 raw-count winner and a smaller 3x3 denser loser;
- `area`: a 3x3 raw-count winner and a larger 4x4 lower-count loser.

The optional third frame is 3x4 or 4x3 with still fewer cells. Any consecutive three demonstrations include both parity classes, and all four possible query rotations of a four-pair bundle leave both classes among the three demonstrations. The `rival_kind` exact axis allows targeted generation; `lesson_identifiable` rejects a lesson that fails to refute either rival.

## D3 — Construct uniqueness with bounded counts

**Decision.** `winner_count` is 6–8 and `count_margin` is 1–2. The runner-up therefore has 4–7 cells, and an optional third frame has one fewer again. This makes the count winner unique without rejection sampling and keeps every pattern nontrivial.

**Alternatives considered.** Wider count ranges would permit empty/near-empty interiors or exceed the 3x3 rival capacity. A fixed count would reduce visual and combinatorial diversity. Relying on canonical top-left tie behavior was rejected for generated training lessons because ties make the intended selection rule harder to infer.

**Limit.** Generated data does not teach the top-left tie break; the five canonical pairs remain the retained authority evidence for ties.

## D4 — Anchor canonical profiles without collapsing the curriculum

**Intermediate failure.** The first repaired sampler produced canonical-size/palette support only in the easy band.

**Decision.** Every fourth *unoverridden* sample selects one of the five exact canonical `(height, width)` profiles and uses three interior colors, yielding the canonical five-color palette. The other three quarters retain 13–20 by 14–22 canvases and difficulty-aware variation. Any explicit override bypasses anchoring so exact controls remain exact.

**Evidence.** The final profile gate found 18 exact hits in 60 draws: 6/20 in each band, with zero crashes (`checks/after-final-v22/checks/75be7448827f_after_profile_floor.json`).

## D5 — Expose only observable exact controls

**Original choice.** The baseline accepted legacy pseudo-controls such as palette and texture labels without changing output.

**Decision.** Advertise only six measurable controls: `grid_h`, `grid_w`, `n_frames`, `winner_count`, `count_margin`, and `rival_kind`. Validate sample index, difficulty, keys, types, and ranges before generation. `observe_overrides` independently recovers all six values from the grid.

**Evidence.** The final override matrix made 25,560 accepted calls across 284 cases and three bands with zero findings, zero warnings, and strict unknown-key rejection (`checks/after-final-v22/checks/75be7448827f_after_override_results.json`).

## D6 — Validate the full frame grammar

**Decision.** `self_check` parses the grid rather than checking only shape. It requires a rectangular integer 0–9 grid, two or three exact hollow color-1 rectangles, nonoverlap, one non-frame color per interior, distinct interior colors, nonempty patterns, and no stray foreground outside interiors.

**Alternatives considered.** Reusing the output oracle as validation would conflate lawfulness with labeling. Weak pixel-count checks would miss broken borders and stray colors. The independent task tests therefore use a separate parser and explicit structural mutations.

## D7 — Bind semantics at grid and lesson levels

**Decision.** Declare `highest_density` and `largest_area` rivals, paired witnesses, canonical shortcuts, and lesson competitors. `lesson_identifiable` requires demonstrations to refute both. `EXAMPLES_NEEDED=3` matches the alternating schedule.

**Evidence.** The final semantic gate had 600/600 strict lawful draws, 60/60 successful density witnesses, 60/60 successful area witnesses, and 12/12 identifiable smoke lessons. The larger census materialized 300/300 three-demo lessons and 1,200/1,200 query rotations with zero ambiguity, errors, or hook warnings (`checks/lesson-census-v22.json`).

**Limit.** These results cover declared rivals and the production sampler; they are not a proof against every possible hypothesis.

## D8 — Leave the Racket authority unchanged

The generator was wrong; the selected rule was consistent with all five canonical pairs and the intended task. I pinned `RULE_HASH = "6f03f2e69da2"` and changed no Racket source. Rule smoke, Racket lint, authority sync, and task-local Racket parity all pass.

## Native parametric review — assignment `review-691290efe138b129`

A task-local native family was added without changing the approved production
generator or canonical puzzle data. `selection_metric=raw_count` returns the
exact canonical Racket source. `selection_metric=occupied_density` parses the
same hollow frames and count/area table, then chooses the first frame with the
maximum exact occupied fraction by cross multiplication. The setting-neutral,
prefix-stable sampler supports 2–6 demonstrations and 1–4 queries and includes a
substantive 30×30 case.

The complete staged task suite passed 118/118 tests. A bounded protected-Racket
audit covered 12 episodes, 92 selected labels, 276 executions, nine declared
rivals, and 48 query-separation checks with zero findings. Native qualification
passed both settings on seeds 0 and 17. The source-bound causal replay confirmed
that replacing the raw-count-selected bounding box with the density-selected
one changes the final crop. Sixteen saved one-query public projections passed
structural and leakage checks. These are finite reviewer checks, not owner
acceptance, universal identifiability, measured model gain, or training
admission.
