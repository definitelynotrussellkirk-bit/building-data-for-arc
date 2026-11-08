# Working notes: 9758187b19ad

## 2026-10-02 first adversarial distribution review

Two simple rivals reproduce all three canonical pairs exactly:

1. transform and stamp only the first marker found for each marker color; and
2. extract stencil cells only from the first five columns.

The baseline generator did not reliably teach against the first rival in every three-demo window and never refuted the second because every source stencil was confined to the left five-column strip. It also used six immutable masks and a fixed 2×3 bank of right-side stamp slots.

Version `3.1.0` made these generator-only changes:

- connected 5–8-cell morphology is sampled within each canonical-linked bounding-box and top-left-anchor class, retaining the original base mask with 20% probability;
- period-5 source-side and period-7 marker-count schedules are crossed with the period-6 morphology schedule;
- a general non-overlapping rectangle packer replaces the fixed right-side slot bank;
- both canonical-fitting rivals are declared and checked by exact disagreement witnesses and lesson-level identifiability; and
- positive structural predicates are explicitly classified as branch witnesses for the strict after-phase semantic gate.

## 2026-10-02 second adversarial round

A full cyclic-window search found four additional canonical-fitting rules that version `3.1.0` did not always disambiguate:

- `canonical_template_boxes_only` and `canonical_grid_sizes_only` each survived 35/210 three-demo windows in every band and failed all 35 corresponding queries;
- `first_five_template_cells` survived 17/16/20 windows in easy/medium/hard and failed 9/8/13 corresponding queries; and
- `ignore_color_one` survived one window in each band and failed that query.

The exact pre-fix counts and starts are retained in `checks/round2-before/canonical_shortcut_window_probe.log`. A fifth exploratory correlation, treating every non-`2` color as a singleton, fit the canonical pairs but already survived zero generated lesson windows, so it did not require a distribution change.

Version `3.2.0` makes the minimum curriculum repair:

- profile order alternates canonical and expanded grid/template dimensions, so every three-demo window contains a noncanonical grid size and template box;
- a period-3 feature-breaker schedule forces one example in every three to contain color `1` and more than five stencil cells;
- the four newly ambiguous rivals are executable semantic rivals, lesson competitors, exact witnesses, and canonical-shortcut declarations;
- `CANONICAL_SHORTCUTS` now contains only the six named rivals that actually fit all public pairs; all ten semantic rivals remain lesson-scored; and
- `workspace/distribution_probe.py` version 2 derives its checks from generator declarations, exhausts every rival over the full schedule, checks the four feature guarantees, and retains one exact generated disagreement case per rival.

Measured second-round evidence is under packet-root `checks/round2-after/` and `checks/round2-final/`. The v2 probe reports 4,320/4,320 unique ordinary inputs, 720/720 valid boundary cases, full 54/54 categorical cross support in each band, zero survivors for all ten rivals across 630 cyclic lesson windows, and no missing feature window. The canonical Racket authority was not edited.
## Current reviewer considerations

Source SHA-256: `e2b70e09c60cf10aa7a8f4a1b27123741c1925833dd9ccd8755152218286a31e`.

# Decisions for generator 9758187b19ad

This file records the input-distribution choices made during this review, why they were made, alternatives considered, the probes used, and known failure modes. The canonical rule and Racket authority were not changed.

## D1. Preserve the transformation rule and Racket authority

**Choice.** Keep the existing intended semantics: extract the non-marker colored template; stamp it at every marker; recolor 3/4/5/6 as specified by the task; and apply the marker-specific geometric transform. Keep Racket rule hash `bb29b95b6fe8` unchanged.

**Original rationale.** Prior evidence already corrected marker 6 to clockwise rotation. The before battery showed authority synchronization, Racket lint, rule smoke, execution, and Python/Racket parity were green. I found no canonical counterexample to the current rule.

**Alternatives rejected.** Changing marker-6 orientation again; simplifying transformations; changing the canonical row; replacing the Racket implementation merely to mirror Python refactoring.

**Probes.** Before and final after batteries; canonical rival checks; rule-smoke and authority-sync reports under `checks/before/`, `checks/after/`, and `checks/round2-final/`.

**Failure modes / limitations.** Canonical demonstrations remain finite, so another semantically plausible rule could exist. This review names six concrete canonical-fitting shortcuts and retains the authority rather than claiming uniqueness from examples alone.

## D2. Retain six morphology classes, but procedurally enumerate lawful members

**Choice.** Preserve each profile's bounding-box dimensions and top-left occupancy class, but sample from all 8-connected masks with 5–8 cells that span every row and column of that box and satisfy the top-left condition. Keep the original mask with probability 0.20.

**Original rationale.** The baseline used six literal masks. Those masks grounded the generator in the canonical examples but exposed a six-template lookup shortcut and weak shape support.

**Alternatives considered.** (a) Keep the six masks unchanged; (b) random-walk shapes; (c) unconstrained random cell sets; (d) enumerate a constrained family. I chose (d), because it is deterministic to validate, preserves the semantic profile distinctions, and cannot silently produce disconnected or shrunken shapes. The 20% base-mask branch retains direct canonical grounding.

**Probes.** `test_profile_constrained_morphology_is_not_a_six_mask_lookup_table`; the ordinary census in `checks/round2-final/9758187b19ad_distribution_probe_v2.json`; focused tests in `checks/round2-after/focused-source-tests-final.log`.

**Measured result.** In 4,320 ordinary draws, observed unique normalized masks by profile were 530, 72, 6, 84, 19, and 26 in the final v2 probe. The six-mask baseline is no longer a complete lookup table.

**Failure modes / limitations.** The smallest legal class has only six masks because its bounding box and connectivity constraints are tight. Shape probabilities are uniform over candidate masks, not balanced over higher-level visual motifs. The procedure deliberately does not expand bounding-box families beyond the six retained profile classes.

## D3. Cross source position independently of morphology

**Choice.** Schedule source side with period 5: `left, middle, left, right, middle`, independently of the period-6 morphology profile.

**Original rationale.** In every canonical example and in the baseline generator, the source template lived in the left strip. A rival that reads source colors only from columns 0–4 fits all canonical pairs.

**Alternatives considered.** Pure random side selection; one side permanently assigned per morphology; always center; fixed left strip. Pure randomness could produce three-demo lessons with no counterexample. Profile-local assignment aliases side with shape. The coprime deterministic schedule guarantees recurring evidence and full crossing.

**Probes.** Exhaustive 210-start lesson-window regression across every difficulty band; all 54 profile × side × marker-count combinations per band; exact generated disagreement at easy seed 0, sample index 3.

**Failure modes / limitations.** The schedule is intentionally non-uniform: left and middle each occur twice per five samples, right once. It guarantees semantic coverage, not perfectly uniform positional frequency. A learner could in principle infer schedule order if sample indices are exposed externally, although the rule remains necessary to produce outputs.

## D4. Cross marker multiplicity independently of morphology

**Choice.** Schedule marker count with period 7: `4, 5, 4, 6, 5, 4, 6`, independently of profile and source side.

**Original rationale.** The canonical examples contain exactly one marker of each code. The baseline permitted repeats only in some profiles, so a three-demo lesson could place all repetition evidence in the hidden query. A rival that stamps only the first marker of each code fits every canonical pair.

**Alternatives considered.** Always exactly four markers; random count 4–6; force repeated markers only in hard mode; profile-local counts. Randomness and hard-only evidence do not guarantee identifiability in an arbitrary three-demo lesson. The period-7 schedule guarantees every cyclic three-sample window has at least five markers in one demonstration and therefore at least one repeated marker code.

**Probes.** Canonical shortcut test; exhaustive 630 lesson windows; exact generated disagreement in `checks/round2-final/9758187b19ad_distribution_probe_v2.json`; final strict semantic gate.

**Failure modes / limitations.** The schedule tests repetition of marker codes but does not balance which particular code is repeated. It guarantees one repeated code, not every code repeated within each lesson.

## D5. Replace reserved slots with full-grid rectangle packing

**Choice.** Randomly pack the actual source bounding box and every transformed stamp bounding box across the full grid. Account for width/height exchange under color-6 rotation. Constrain only the source to its scheduled left/middle/right region; reject overlap and out-of-bounds placements.

**Original rationale.** The baseline reserved the first five columns for the source and used six fixed 4×4 destination slots. Those coordinates exposed scaffolding unrelated to the abstract task.

**Alternatives considered.** Preserve fixed slots; jitter within fixed slots; rejection-sample individual cells; pack exact rectangles. Exact rectangle packing gives a simple invariant: if boxes do not overlap, the reconstructed stamps cannot overlap. It also supports arbitrary legal shape dimensions without hand-maintained slots.

**Probes.** `test_general_packer_places_valid_nonoverlapping_boxes_for_all_source_sides`; self-check stage; 720-case boundary matrix over grid/profile/marker extremes; override stage.

**Failure modes / limitations.** Greedy randomized packing is not a complete bin-packing solver. A legal arrangement may exist even if a specific attempt fails; bounded retries mitigate this. Current dimensions and marker maxima passed all sampled boundary cases, but future larger profiles or more markers may need backtracking.

## D6. Make shortcut claims and witness ownership explicit

**Choice.** Add executable named rivals and exact witnesses for the six canonical-fitting shortcuts found in both review rounds. Keep all ten semantic rivals as lesson competitors, but put only rules that reproduce every public pair in `CANONICAL_SHORTCUTS`. Classify positive structural predicates separately in `BRANCH_WITNESSES`.

**Original rationale.** The initial after implementation correctly produced shortcut counterexamples, but strict semantic policy rejected nine unclassified positive witnesses. The second round also found that aliasing `CANONICAL_SHORTCUTS` to all semantic rivals mislabeled four rules that do not fit the public pairs. Treating all witnesses as rival refutations would make the metadata dishonest.

**Alternatives considered.** Remove the positive witnesses; weaken strict policy; attach arbitrary rivals to them; add explicit branch classification. Explicit classification preserves both coverage observability and falsifiable rival claims.

**Probes.** Retained failed semantic run under `checks/after-failed-semantic/`; red/green regression logs `checks/tdd-red-branch-witness.log` and `checks/tdd-green-branch-witness.log`; final semantic report.

**Failure modes / limitations.** Metadata only checks the named rivals. It cannot prove absence of all possible shortcuts. Future structural witnesses must also be deliberately assigned to a rival or to branch coverage.

## D7. Preserve public axes and grid-size envelope

**Choice.** Keep existing public override axes, grid dimensions, palette semantics, and difficulty bands. Reject unknown override keys. Improve their internal crossing rather than adding speculative knobs.

**Original rationale.** Existing consumers and the battery depend on the declared interface. The defect was distributional aliasing, not a missing public configuration surface.

**Alternatives considered.** Add `source_side`, `profile`, or `marker_count` as public axes; shrink the grid to simplify packing; enlarge grids to avoid packing pressure. Those changes would widen the contract or hide packing defects without being required by the canonical task.

**Probes.** Final override contract, grammar, diversity, self-check, profile-floor, and boundary-matrix results.

**Failure modes / limitations.** Internal scheduled factors are not directly overrideable. This is intentional for the current task, but future maintainers may decide diagnostic-only overrides are useful.

## D8. Retain a reusable adversarial distribution probe

**Choice.** Add `workspace/distribution_probe.py` as a non-executable, standalone review tool.

**Original rationale.** The generic battery samples semantic behavior but does not exhaust a 210-step schedule superperiod or encode these task-specific rivals. Future edits need a cheap way to detect recurrence of any declared rival or factor aliasing.

**Alternatives considered.** Put every census in production tests; rely only on the generic semantic gate; leave a one-off notebook. The standalone script keeps heavy review evidence reproducible without making ordinary unit tests slow.

**Probes and outputs.** Run from `repo` with `python3 generators/9758187b19ad/workspace/distribution_probe.py --seeds 80 --out ../checks/round2-final/9758187b19ad_distribution_probe_v2.json`. Version 2 derives canonical shortcuts and lesson competitors from generator declarations, checks all four feature guarantees, and stores one exact disagreement case per rival.

**Failure modes / limitations.** This is finite testing, not a proof of every random seed or every future implementation. The schedule-window portion is exhaustive for the current 210-step factor schedule; the morphology and packing census remains sampled.

## D9. Alternate canonical and expanded size profiles

**Choice.** Reorder the six existing profiles as canonical/expanded pairs: `canonical_l`, `wide_zig`, `canonical_cross_empty_corner`, `tall_hook_empty_corner`, `canonical_x`, `asymmetric_square`.

**Rationale.** Version `3.1.0` grouped all three canonical grid/template size classes together. A solver that runs the correct rule only on canonical grid sizes or on canonical template boxes therefore fit 35/210 three-demo windows per band and failed every associated query. Alternation guarantees that every cyclic three-demo window includes both an expanded grid size and a noncanonical template box without adding a new profile or changing public axes.

**Alternatives considered.** Randomly shuffle profiles; add a seventh profile; enlarge every profile. Random ordering does not give a lesson-level guarantee, a seventh profile changes the schedule period and balance, and enlarging every profile discards useful canonical grounding.

**Evidence.** `checks/round2-before/canonical_shortcut_window_probe.log`; exact red/green regressions in `checks/round2-before/tdd-red-round2-shortcuts.log` and `checks/round2-after/tdd-green-round2-shortcuts.log`; final exhaustive v2 probe.

**Limitations.** The curriculum still exposes a deterministic order. This is acceptable because sample indices are generation controls, not input features; a future sampler that groups nonconsecutive indices should rerun the exhaustive window probe for its own lesson assembly policy.

## D10. Guarantee color and stencil-cardinality evidence in every lesson

**Choice.** Add the period-3 schedule `(False, True, False)`. On the designated sample, require a 6–8-cell stencil and require color `1` to be present.

**Rationale.** The canonical stencils all have five cells and omit color `1`. The `first_five_template_cells` rival survived 17/16/20 windows, while `ignore_color_one` survived one window per band. A dedicated middle demonstration is the smallest deterministic repair: it makes both omitted features visible without forcing every example away from the public morphology.

**Alternatives considered.** Always use more than five cells; always require color `1`; rely on random color assignment; add independent period-2 and period-3 schedules. Always-on constraints narrow diversity, randomness leaves ambiguous windows, and separate schedules are unnecessary because one example can refute both rules.

**Evidence.** The final v2 probe reports zero missing starts for `more_than_five_template_cells` and `contains_color_one` in all 630 windows, and zero survivors for both corresponding rivals.

**Limitations.** This guarantees presence, not balanced frequency or position, of color `1`. The ordinary census is intentionally mixed: 3,741/4,320 draws include color `1`, while 579 omit it.

## D11. Keep the probe declaration-driven and exact

**Choice.** Upgrade the retained probe to schema `9758187b19ad-distribution-probe-v2`. Enumerate `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS` directly rather than hard-coding names; exhaust the complete schedule period; retain exact inputs, outputs, hashes, and first disagreements for every rival.

**Rationale.** The v1 probe silently covered only the two first-round shortcuts. That made it easy for later metadata additions to outgrow the audit tool. Declaration-driven iteration makes a new rival automatically enter canonical-fit checking, all-window lesson checking, and exact-witness capture.

**Alternatives considered.** Keep adding rival-specific code; rely on the sampled semantic gate; store only aggregate counts. Hard-coded names drift, sampled lessons can miss schedule aliases, and aggregate counts are insufficient for replay or diagnosis.

**Evidence.** `test_distribution_probe_round2.py` was red against v1 and green against v2. The 80-seed run checks ten rivals, six canonical-shortcut claims, 630 lesson windows, 4,320 ordinary draws, and 720 boundary cases with no failure.

**Limitations.** The schedule audit is exhaustive only for declared deterministic schedule state. Random morphology, color assignment, and packing remain sampled; exact disagreement cases establish existence, not frequency outside the measured census.
