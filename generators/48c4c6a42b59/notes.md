# Working notes: 48c4c6a42b59

## Review diagnosis — 2026-10-02

The immutable version-2.1.0 baseline had a correct authoritative rule but an unreliable generator contract:

- missing `RULE_HASH`;
- dead/singleton pseudo-axes and ignored palette/texture declarations;
- 9,391 override findings across 77,760 draws;
- unknown override keys accepted;
- generated 3–6-cell objects versus canonical 6–11-cell objects;
- 0/60 exact canonical-profile hits and no easy/hard support;
- degenerate negative textures mixed into the ordinary domain;
- no semantic contract.

Baseline battery: 7 green, 2 advisory, 3 failed (`lint`, `defect_lint`, `override`). The Racket rule, grammar, and authority sync were already healthy, so no authority change was justified.

## Version 3.0.0 design

- Exact axes only: `grid_h` 11–13, `grid_w` 11–13, `n_blobs` 2–3.
- Keyed deterministic draws and explicit unknown-override rejection.
- Seven normalized canonical source morphologies plus four lawful rectangular extrapolations; horizontal mirrors accepted by validation.
- Object size 6–11, bbox dimensions 3–5, distinct color per object.
- Four-profile deterministic curriculum: `canonical_square`, `mixed_bbox`, `size_contrast`, `palette_counterexample`.
- Bounded backtracking placement with source halos and disjoint transformed footprints.
- Every object is effectful; at least one local mirror axis differs from the canvas axis.
- Independent Python oracle, eight rivals, eight witnesses, and lesson-identifiability checking.
- Mutation-sensitive structural checker.

## Test-driven implementation record

The focused tests were written against the intended contract before implementation. The initial run against the old generator produced seven failures and one pass. During the green step, the suite exposed a real defect: one rectangular shape constant was not normalized/sorted and therefore drifted from the morphology set. Normalizing it at the source made the full suite pass.

Current focused result: 8 passed.

## Final evidence

- Official after battery: 12 green, 0 advisory, 0 failed.
- Override: 0 findings over 2,880 draws / 32 cases.
- Canonical profile: 29 exact and 34 envelope hits out of 60; every band supported.
- Semantic gate: PASS; strict 121/600; all 8 witnesses fire; all 8 rival claims verify; 12/12 lessons identifiable.
- Smoke/parity: 120 applications, zero crashes, 120 distinct outputs, zero identity cases, 120/120 Python/Racket parity.
- Fresh solve: first revision passed 3/3 visible examples; earlier rule exposure disclosed; no reference consulted during solve; private query score withheld.

## Known limits

The morphology family is finite, the exact axis range is canonical-centered, all generated objects are effectful, and the named rivals are not exhaustive. These are explicit curriculum choices rather than hidden generator behavior.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `207c8b07b5b5227049e440a50288cf2a0b4eab132fa52b519824c0da9b3c18b5`.

# Decisions for `48c4c6a42b59`

## 1. Keep the canonical Racket rule unchanged

**Original rationale:** The imported notes did not state a rationale. The baseline smoke, Racket lint, grammar, and authority-sync checks were already green, and manual comparison with the canonical pairs showed the rule was correct.

**Decision:** Change only the Python generator and its task-local tests. Pin the existing rule with `RULE_HASH = "cecf4f1691f5"`.

**Alternatives considered:** Rewrite or simplify the Racket rule; change the canonical row; make the Python oracle authoritative.

**Probe:** The after smoke test applied the Racket rule 120 times with zero crashes, zero identity cases, and 120/120 Python-oracle parity.

**Failure modes / limits:** Python and Racket could drift later. The pinned hash and parity stage now make that drift visible.

## 2. Replace the broad metadata surface with three exact axes

**Original rationale:** Unknown. The baseline declared grid dimensions, object count, color count, palette size/kind, texture, position bias, and density, but multiple fields were dead, redundant, or singleton labels.

**Decision:** Retain only `grid_h`, `grid_w`, and `n_blobs`. They are real input properties, keyed draws, exact overrides, and recoverable from the returned grid.

**Alternatives considered:** Repair every old axis; mark singleton fields diagnostic; keep palette as a fourth exact axis.

**Probe:** The override stage exercised 32 cases over all three bands and 2,880 draws with zero findings. Focused tests cover every boundary corner and unknown-key rejection.

**Failure modes / limits:** Palette and morphology are still varied, but not externally overrideable. Add them as axes only if downstream users need controlled interventions and the observable contract can be made exact.

## 3. Use 11–13 rows and columns

**Original rationale:** The baseline summary described roughly 9–12, while actual difficulty paths often generated 9–10 and contradicted the declared 8–13 override range. The canonical canvases are 11×11, 12×12, and 13×13.

**Decision:** Set both exact domains to 11–13. Difficulty biases keyed draws inside the same legal domain rather than changing legality.

**Alternatives considered:** Preserve 8–13; use only the three square canonical sizes; support a much wider extrapolation range.

**Probe:** Canonical-profile support increased from 0 exact and 1 envelope hit to 29 exact and 34 envelope hits out of 60, with support in every band.

**Failure modes / limits:** The model receives less small-canvas extrapolation. This is deliberate because the immediate objective is high-quality canonical-centered training data.

## 4. Generate exactly two or three objects

**Original rationale:** The baseline allowed 1–4 and even treated `single_blob` as a texture, despite canonical examples containing multiple objects and the teaching goal requiring object-wise generalization.

**Decision:** Use two or three objects, each in a distinct nonzero color.

**Alternatives considered:** Include one-object warmups; retain four-object hard cases.

**Probe:** The semantic census includes a `three_objects` witness, and object-count overrides are exact. The one-object mutation is rejected.

**Failure modes / limits:** Four-object crowding is not taught. It can be added later only with placement and collision evidence.

## 5. Anchor morphology to the canonical inputs

**Original rationale:** The baseline sampled 3–6-cell blobs, while canonical objects occupy 6–11 cells and 3–5-cell local boxes.

**Decision:** Encode all seven normalized source morphologies present across the five canonical inputs and add four connected rectangular-box extrapolations. Allow their horizontal mirrors in validation. Require sizes 6–11 and box dimensions 3–5.

**Alternatives considered:** Random walks; polyomino enumeration; arbitrary connected subsets; exact replay of canonical inputs only.

**Probe:** All five canonical input/output pairs pass `self_check`, `strict_canonical_like`, and the Python oracle. Defect lint and profile floor are green.

**Failure modes / limits:** A finite library can create morphology memorization. The schedule, colors, positions, counts, dimensions, aspect ratios, and size contrasts reduce that risk, but a future procedural connected-shape family would broaden support further.

## 6. Make every generated object effectful

**Original rationale:** The baseline mixed `all_lr_symmetric` into the ordinary texture domain, creating identity examples that failed its own intended teaching invariant.

**Decision:** Every source object is asymmetric under local horizontal reflection; every generated scene changes.

**Alternatives considered:** Mix a small lawful symmetric no-op branch; require only one object to change.

**Probe:** The smoke stage reports 120/120 fired and zero identity outputs. `every_object_changes` fires on 600/600 semantic draws.

**Failure modes / limits:** This omits the lawful already-symmetric no-op case. It is a reasonable later curriculum branch, but only after it is explicitly named and paired with enough effectful demonstrations to avoid an identity shortcut.

## 7. Separate both sources and transformed footprints

**Original rationale:** The baseline intended isolated bounding boxes, but `bboxes_overlap` was admitted and passed self-check in samples.

**Decision:** Use bounded backtracking. Source cells receive a one-cell Chebyshev moat; complete local mirror unions must be pairwise disjoint.

**Alternatives considered:** Rejection sampling; fixed slots; permit transformed overlaps when colors agree.

**Probe:** All override draws and 600 semantic census draws generated without crashes; targeted collision and same-color bridge mutations are rejected.

**Failure modes / limits:** Backtracking cost grows rapidly with larger grids, shape sets, or object counts. It is bounded and cheap for at most three 5×5 footprints.

## 8. Force a local-versus-global reflection witness

**Original rationale:** Unknown. Without positional intervention, centered objects can make local bounding-box reflection indistinguishable from global canvas reflection.

**Decision:** During placement, require at least one object's local horizontal axis not to equal the canvas axis.

**Alternatives considered:** Rely on random placement; add a post-generation rejection; create a dedicated position axis.

**Probe:** `bbox_local_not_global` fires on 600/600 semantic draws, and its named global-reflection rival is refuted in every checked claim.

**Failure modes / limits:** This witnesses the global shortcut but does not cover every position-dependent wrong rule. A generic nuisance-counterfactual gate is proposed in `QUESTION_ANSWER.md`.

## 9. Use a four-profile deterministic curriculum

**Original rationale:** The baseline had labels such as `default`, `warm`, `cool`, and `varied`, but they were byte-identical in sampled draws.

**Decision:** Schedule four semantically meaningful profiles: canonical squares, mixed box aspect ratios, size contrast, and a palette branch that excludes color 8. Four consecutive sample indices cover all profiles; band offsets prevent a fixed profile from becoming synonymous with difficulty.

**Alternatives considered:** Pure random selection; separate override axes for every profile property; many narrow profiles.

**Probe:** The semantic census saw all four profiles in every band, and 12/12 requested lesson windows were identifiable.

**Failure modes / limits:** A four-cycle is predictable. Seed-dependent geometry, color, dimensions, count, and placement still vary; the profile schedule itself is intentionally inspectable and reproducible.

## 10. Use distinct colors as object identity

**Original rationale:** The task's canonical scenes use colored objects, and same-color disconnected components make object ownership more ambiguous for both generation and checking.

**Decision:** Sample distinct colors for the two or three objects. In the palette-counterexample profile, sample from colors excluding 8.

**Alternatives considered:** Repeated colors with spatial-component ownership; fixed canonical colors; fully controlled palette axes.

**Probe:** Self-check requires each nonzero color to form exactly one component. The `palette_without_eight` witness fired 489/600 times and refuted the color-8-only shortcut.

**Failure modes / limits:** The distribution does not teach multiple disconnected objects of one color. That is lawful under a component-based reading but would need explicit ownership tests.

## 11. Add an independent oracle, rivals, and lesson validation

**Original rationale:** The baseline had no semantic contract and therefore no automated statement of what examples were supposed to distinguish.

**Decision:** Implement an independent Python oracle, eight plausible wrong rules, eight witnesses, witness-to-rival mappings, and `lesson_identifiable` over demonstrations plus query.

**Alternatives considered:** Depend only on output diversity; compare only to identity; use model-based ambiguity scoring.

**Probe:** The semantic gate reports 121/600 strict draws, 8/8 witnesses firing, 8/8 rival claims verified, and 12/12 lesson windows identifiable.

**Failure modes / limits:** Named rivals are not exhaustive. They are executable documentation and a floor, not a proof that no shortcut exists.

## 12. Add focused mutation and reproducibility tests

**Original rationale:** No task-local regression suite was present.

**Decision:** Add eight tests covering canonical ownership, exact overrides, three-band support, schedule windows, rival claims, targeted invalid mutations, negative recombination, deterministic replay, fresh object returns, and process-global RNG purity.

**Alternatives considered:** Rely only on the official battery; snapshot generated grids; test implementation details alone.

**Probe:** The test was first observed failing against the old implementation, exposed a non-normalized rectangular shape during implementation, and now passes 8/8.

**Failure modes / limits:** The official battery does not currently discover task-local pytest files automatically; the test log is included separately and tooling feedback requests a dedicated stage.
