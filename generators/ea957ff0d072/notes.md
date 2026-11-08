# Working notes: ea957ff0d072

## 2026-09-28 review

### Baseline diagnosis

The imported 3.1.0 generator described a different, much narrower task: an edge wall, one shared marker direction, and every object moving toward that wall. That grammar rejected all three canonical inputs. The canonical examples instead contain an internal full-height wall, mixed marker colors, and a row-major sequential update in which moved objects can affect later marker selections and stopping positions.

The retained before battery (`checks/before`) finished 6 green, 1 advisory, and 5 failed. Important failures were:

- no `RULE_HASH`, four behaviorally dead texture/palette axes, and overlapping ordinary/degenerate textures;
- all three canonical inputs rejected by `self_check`;
- canonical-profile support 0/60;
- no semantic contract;
- 17,261 override findings over 89,550 draws and 995 cases, including silent unknown-key acceptance.

The morphology-only distribution gate passed the wrong-task baseline. This is useful negative evidence: matching coarse marginals did not establish semantic fidelity.

### Rule decision

The canonical Racket rule was not changed. Its normalized hash is `d849dec31c02`, it solves every canonical pair, and its selected authorities pass execution parity. The defect was the generator and its lesson distribution.

### Generator redesign

Version 4.0.0 uses four repeating constructive profiles:

1. `canonical_independent` — canonical 8x12 scale, internal wall, independent slides;
2. `canonical_order_block` — canonical 9x12 scale, an earlier move that affects a later move;
3. `canonical_three_way` — canonical 9x13 scale, three objects and three directions;
4. `attachment_counterexample` — mixed marker attachment that separates marker color from marker position.

Every four consecutive examples include every profile and all marker colors 1..4. Declared axes are now only observable, exact controls: `grid_h`, `grid_w`, `n_objects`, `wall_position`, and `marker_attachment`. Unknown overrides fail loudly. The obsolete texture, palette, position-bias, wall-side, and redundant color-count axes were removed.

A pure Python mirror pins the intended semantics and is checked against the real Racket authority. Named rival rules cover the strongest public shortcut (`move_away_from_marker`), wall attraction, reverse scan order, and one-step movement. `lesson_identifiable` requires a four-demo lesson to refute all four.

### Red/green findings during implementation

- Initial rival code cleared objects before inferring marker adjacency, so `move_away_from_marker` accidentally fell back to the true color direction. A failing rival test exposed this; the rival now derives direction from the original component cells.
- The strict semantic gate found one randomized easy lesson, seed `276603472566824`, whose optional third object moved next to the later mixed marker and dynamically stole its selection. The exact replay was added as a regression; the third object is now confined to the top band.
- The first green battery still showed low anchor diversity (mostly color permutations). Semantics-preserving horizontal reflection and complementary seed-coupled vertical reflection increased pair uniqueness to 51% while preserving the all-four-directions guarantee.
- Independent random vertical flips initially allowed both vertical anchors to lose marker 4 in the same lesson. The existing four-demo test failed. Coupling the two profile orientations in complementary phases fixed the root cause.

### Final retained evidence

The clean after battery in `checks/after` is 12/12 green. The semantic gate reports 600/600 strict-valid draws, 3/3 canonical inputs accepted, 4/4 witnesses firing, 4/4 rival claims verified, and 12/12 sampled lessons identifiable. The canonical-profile gate reports 41/60 exact-profile and 42/60 envelope support. Diversity reports 51% unique inputs and outputs over 300 pairs with no flags. Override checking reports 20,520/20,520 accepted draws over 228 cases and zero findings.

### Remaining limitations

This remains a deliberately bounded constructive family: one vertical color-8 wall, two or three distinct 3–4-cell objects, and four scene templates plus reflections. It does not attempt arbitrary obstacle fields, repeated object colors, larger polyominoes, or horizontal walls because those are not needed to identify the pinned canonical rule and would increase construction and dynamic-selection risk. Difficulty mainly changes the exploratory fourth slot's dimensions and some axis draws; the three canonical anchor dimensions stay fixed by design.
## Current reviewer considerations

Source SHA-256: `29956569638659c4561a7c9b06eec798d842609a3f51de202780ee40d25de2cb`.

# Decisions: ea957ff0d072

## D1 — Preserve the canonical Racket rule

**Original rationale:** Unknown beyond the retained canonical program and public examples. The active authorities already agreed.

**Chosen approach:** Leave the Racket source unchanged, pin its normalized hash (`d849dec31c02`), and repair the generator around it.

**Alternatives considered:** Rewrite/simplify the Racket; change semantics to match the old wall-directed generator.

**Probes:** All canonical pairs, real-Racket smoke, authority-sync execution parity, and Python-mirror parity on 120 generated grids.

**Failure modes / limitations:** The Python mirror duplicates semantics and could drift; the rule hash, canonical-pair tests, and 120/120 Racket parity make drift visible. Existing nonblocking Racket style findings remain.

## D2 — Model the wall as one vertical obstacle, not a destination

**Original rationale:** The baseline assumed a wall on any outer edge and generated all motion toward it. That rationale is contradicted by canonical examples with an internal full-height vertical wall and independently directed motion.

**Chosen approach:** Emit one full-height color-8 column, at an edge or interior position, while allowing movement toward, away from, or parallel to it.

**Alternatives considered:** Arbitrary obstacle fields; horizontal walls; edge-only walls.

**Probes:** Canonical acceptance, profile floor, `move_toward_wall` rival, and `wall_is_obstacle_not_destination` witness (600/600 final draws).

**Failure modes / limitations:** The generator does not explore horizontal or fragmented walls. That is a conscious grammar bound, not a claim that the executable rule cannot accept other blockers.

## D3 — Use two or three distinct 3–4-cell objects

**Original rationale:** The baseline allowed 1–5 blobs and 2–4-cell growth but often failed to place the requested number; color-count axes were redundant and non-exact.

**Chosen approach:** Construct exactly 2–3 distinct-color, 4-connected objects of 3–4 cells.

**Alternatives considered:** Random grown blobs; repeated object colors; 1 or 4+ objects; larger shapes.

**Probes:** Structural self-check, mutation sensitivity, exact `n_objects` overrides, all canonical inputs, and rule smoke.

**Failure modes / limitations:** Shape vocabulary is template-bounded. Reflections and four profiles vary geometry, but this is not a uniform polyomino sampler.

## D4 — Repeat a four-profile lesson schedule

**Original rationale:** Unknown. The old generator had no lesson-level contract and could repeatedly teach the same wall-directed shortcut.

**Chosen approach:** `EXAMPLES_NEEDED = 4` with residues for independent, order-blocking, three-way, and attachment-counterexample profiles. Any four consecutive sample indices contain all four.

**Alternatives considered:** Pure random mixtures; larger lessons; one monolithic random scene builder.

**Probes:** Every start residue, three difficulty bands, multiple seeds, and the semantic gate's 12 independently sampled lessons.

**Failure modes / limitations:** The schedule is visibly periodic. Periodicity is accepted here because it gives a falsifiable teaching guarantee and generation remains varied within profiles.

## D5 — Include a mixed marker-attachment discriminator

**Original rationale:** Every public marker lies behind its object, so marker placement and marker color are observationally confounded. The baseline reinforced the confound.

**Chosen approach:** In the fourth profile, place a color-3 marker beside a horizontal object. The intended rule moves it up; “move away from the marker” moves it horizontally.

**Alternatives considered:** Rely on random marker placement; add a textual hint; use only canonical-shaped examples.

**Probes:** Exact public-pair shortcut fit, exact generated Racket counterexample, 146/600 attachment witnesses, and every four-demo lesson identifiable.

**Failure modes / limitations:** Dynamic selection can be changed by earlier moves. One randomized failure exposed that an optional third object could steal the marker; its placement is now constrained and the exact seed is a regression.

## D6 — Make row-major interaction constructive

**Original rationale:** The canonical program sorts marker positions and mutates the current grid, but the baseline isolated blobs so order was mostly irrelevant.

**Chosen approach:** A dedicated profile creates an earlier move that changes a later move's environment, making reverse order answer-different.

**Alternatives considered:** Detect order witnesses after unconstrained random generation; omit order from the lesson contract.

**Probes:** `reverse_scan_order` rival, row-order witness 592/600, and per-lesson witness requirement.

**Failure modes / limitations:** The exact interaction forms are templated rather than exhaustively varied.

## D7 — Keep only exact, observable override axes

**Original rationale:** The baseline exposed nine axes, including aliases and derived values. Several were dead, boundary values were rejected by difficulty-specific draws, and unknown keys were swallowed.

**Chosen approach:** Keep five independent axes and route every requested value through keyed draws. Reject unknown names/types immediately. Declare no incompatible combinations because every boundary cross-product is constructible.

**Alternatives considered:** Preserve legacy aliases; declare many incompatibilities; silently clamp values.

**Probes:** Task-local full boundary cross-product and official override gate: 20,520/20,520 accepted draws, 228 cases, zero findings.

**Failure modes / limitations:** Removed axes may break callers that depended on undocumented legacy names; loud rejection is preferred to false success.

## D8 — Add an executable semantic contract

**Original rationale:** None existed (`NO_CONTRACT`). Coarse distribution checks passed despite wrong semantics.

**Chosen approach:** Expose strict validation, four named witnesses, four named rivals, the canonical shortcut, and `lesson_identifiable`.

**Alternatives considered:** Rely solely on self-check; rely on morphology/profile gates; document rivals without executable checks.

**Probes:** Semantic gate, exact rival regression tests, canonical shortcut test, and strict 600/600 draw sweep.

**Failure modes / limitations:** The rival set is strong but finite; an unmodeled rival may still fit. The contract is designed to be extended as new shortcuts are discovered.

## D9 — Add reflections without weakening lesson coverage

**Original rationale:** Initial constructive anchors were semantically strong but varied mostly by payload colors, producing a 32% uniqueness warning.

**Chosen approach:** Random horizontal reflection with marker-code swap and complementary seed-coupled vertical reflection across the two vertical-anchor profiles.

**Alternatives considered:** Random independent vertical flips; more scene templates; accept the diversity warning.

**Probes:** Color-permutation ceiling tests, 256-seed orientation tests, every four-demo direction-coverage test, and final diversity gate (51%, zero flags).

**Failure modes / limitations:** Reflection is structured variation, not new topology. Independent vertical flips were rejected because they could simultaneously remove marker 4 from a lesson.

## D10 — Prefer constructive placement over rejection sampling

**Original rationale:** The baseline used blob growth and up to 120 placement attempts, which could underfill requests and made override composition difficult.

**Chosen approach:** Four small builders place known-lawful objects and markers, followed by `self_check` as an internal assertion.

**Alternatives considered:** General random packing with retries; generate-and-filter; constraint solving.

**Probes:** Determinism/freshness/global-RNG test, full axis cross-product, 600 strict semantic draws, and 120 Racket executions.

**Failure modes / limitations:** Constructive templates can overfit. Canonical anchors, dimension exploration, reflections, semantic rivals, and explicit limitations make that tradeoff visible.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-0eac73c41930fb4b:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `29956569638659c4561a7c9b06eec798d842609a3f51de202780ee40d25de2cb`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported bounded clean assessment on the unchanged audited source. 11 reported task tests and strict semantic scope; fixed-parent portability concern remains tool feedback, not a reproduced generator defect. Original report and evidence retained. Training admission unchanged.

### Assessment or prior finding

## ea957ff0d072

**No issue found** in the checked source-bound scope. The audited generator SHA-256 was `29956569638659c4561a7c9b06eec798d842609a3f51de202780ee40d25de2cb`. Its focused task-test stage passed 11 cases (`checks/audit/ea957ff0d072/task-tests/result.json` and `checks/task_tests.xml`), and the strict semantic gate passed (`checks/audit/ea957ff0d072/semantic/checks/ea957ff0d072_audit_semantic_gate.json`). I checked the retained task tests, canonical binding represented in the isolated runtime, executable witnesses/rivals, ordered lessons, and diagnostic rotations. This was not a full battery or universal shortcut search; the fixed-`parents[...]` portability warning is test hygiene feedback, not a demonstrated generator semantic defect. No source was changed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
