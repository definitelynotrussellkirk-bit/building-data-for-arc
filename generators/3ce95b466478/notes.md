# Working notes: 3ce95b466478

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `529c9becc1ddb1c2b51f3cff6f07f047a63d547d1a455fb9a38a8d52c57f5659`.

# Decisions for 3ce95b466478

Each decision is tied to the finding IDs in `REVIEW.md`. “Original rationale unknown” means the inherited packet did not contain enough evidence to recover why that choice was made.

## D1 — Preserve the canonical rule (G3)

**Choice.** Keep the canonical behavior: find 4-connected red components, rank by cell count descending with top-row tie-breaking, select the second, crop its bounding box, and recolor its occupied cells 8.

**Rationale.** All five usable canonical pairs agree with this authority, and `rule_smoke` already showed the executable rule produced their expected outputs. The defect was generator/authority synchronization, not evidence that the rule itself was wrong.

**Alternative rejected.** Rewriting the Racket rule or adopting perimeter ranking. Perimeter ranking is only a canonical-fitting shortcut; [`checks/question_counterexample.json`](checks/question_counterexample.json) proves it disagrees with the selected authority.

**Probe.** Official `rule_smoke`, `racket_lint`, and `authority_sync`, plus an independent Python size oracle in `workspace/reference_probe.py`.

**Limitation.** Text synchronization changed an alternate copy’s hash even though behavior did not change. `REVIEW.md` states this explicitly.

## D2 — Construct layouts instead of rejection sampling (G1)

**Choice.** Place each object in one of six separated 3×3 slots. Use either a 2×3 slot arrangement, or a 3×2 arrangement when height permits. Randomize layout, slot assignment, shape orientation, and within-slot offset.

**Rationale.** The rule requires 3–5 distinct red components plus a separate decoration. Constructive slots guarantee non-touching objects and predictable runtime without repeatedly drawing invalid placements.

**Alternatives rejected.** Free placement with collision/reconnect rejection; this can become seed-sensitive, slow, and hard to reason about under larger objects. Fixed positions; this would leak positional shortcuts.

**Probe.** Determinism, component counts, separation, and distribution tests in `tests/test_generator.py`; 900/900 unique inputs in the final census.

**Failure modes.** The slot geometry bounds shapes to 3×3 and dimensions to grids that admit six slots. It intentionally does not cover arbitrary large polyominoes or all possible lawful layouts.

## D3 — Generate all connected 3×3 polyominoes internally (G1)

**Choice.** Enumerate normalized 4-connected subsets of a 3×3 universe, sample by target size, and apply rotations/reflections where the scheduled witness needs a fixed topological family.

**Rationale.** This gives shape diversity while preserving exact object sizes and connectivity. It also avoids hand-maintaining a small shape list except for the explicit semantic witness.

**Alternative rejected.** Rectangles only. Rectangles would make cell count too correlated with perimeter and bounding-box area, strengthening shortcuts rather than teaching the intended ranking.

**Probe.** Structural validator tests and the finite lesson census’s unique-input and rival-disagreement counts.

**Failure modes.** The generator does not sample every polyomino of a given size uniformly up to free-polyomino equivalence; it samples normalized embeddings within 3×3. No uniformity claim is made.

## D4 — Distinct red component sizes, 3–5 components (G1)

**Choice.** Every generated input contains 3–5 red components with distinct cell counts.

**Rationale.** At least three components are needed for “second-largest” to be substantive. Distinct sizes avoid unresolved ties and match the selected rule’s intended teaching target. Five components increase ranking load on hard examples.

**Original rationale.** The inherited generator also targeted multiple red blobs, but its exact rationale and coverage guarantees were not documented.

**Alternative rejected.** Allowing ties and relying on top-row tie-breaking. The canonical authority has a tie-breaker, but tie-heavy lessons would mix two concepts and weaken the main size-ranking signal. Tie behavior could be a separate future curriculum extension.

**Probe.** `self_check`, component-count overrides, per-band distribution tests, and the stress census.

**Failure modes.** This generator does not teach the top-row tie branch. The contract is deliberately narrower than every executable corner case of the Racket rule.

## D5 — Finite exact dimension controls with canonical weighting (G1)

**Choice.** Advertise exact `grid_h ∈ {8,9,10,16}` and `grid_w ∈ {11,12,13,16}` controls. For default draws, heavily weight one of the five canonical profiles `(8,12)`, `(9,11)`, `(9,13)`, `(10,12)`, `(10,13)` while retaining 16 as a broader endpoint.

**Rationale.** Every band must retain canonical-profile support, and exact controls must be exhaustively checkable. Finite values cover all canonical dimensions and one extrapolative endpoint without combinatorial explosion.

**Alternatives rejected.** Broad integer domains such as all heights 8..16 and widths 11..16. Combined with five public axes, the inherited override checker expanded to 331 cases / 29,790 draws and timed out; see [`checks/override_red.log`](checks/override_red.log). Removing all exact dimension controls was also rejected because it would make declared behavior less inspectable.

**Probe.** Official `profile_floor` and `override`; regression cap `test_override_boundary_matrix_stays_within_stage_budget`; final census canonical-profile hits 772/900.

**Failure modes.** Exact overrides do not expose every validator-legal intermediate dimension. Internal default support is deliberately more important than a maximally broad control surface.

## D6 — Keep only three public exact axes (G1)

**Choice.** Public axes are `grid_h`, `grid_w`, and `n_blobs`. Decoration color and size remain varied internally rather than advertised as exact overrides.

**Rationale.** All public controls are directly observable from the returned grid and can be tested across every band. Decoration variation is semantically incidental and does not justify multiplying the override matrix.

**Alternative rejected.** Five exact axes including decoration color and size. The first implementation was semantically valid but computationally hostile to the existing checker. The red evidence is retained in [`checks/override_red.log`](checks/override_red.log).

**Probe.** `observe_overrides`, exact-round-trip tests, invalid-override tests, official override stage (8.5 seconds in the repaired focused run), and the matrix-size cap.

**Failure modes.** Callers cannot pin decoration details through the public contract. They still vary across seeds and are measured by the census.

## D7 — Band anchors, not band-exclusive domains (G1)

**Choice.** All bands can emit 3, 4, or 5 red components, but easy/medium/hard are weighted toward 3/4/5 respectively. Decoration size is similarly weighted toward 1/2/3.

**Rationale.** Difficulty should shift complexity without making the bands disjoint or causing an exact override to become invalid in a band.

**Alternative rejected.** Easy only 3, medium 3–4, hard 4–5. Early tests exposed that this prevented each band from covering the declared domain and made cross-band exact override semantics inconsistent; see [`checks/test_red.log`](checks/test_red.log).

**Probe.** Per-band distribution tests and official override checks.

**Failure modes.** Difficulty is a soft distributional label, not a proof of human difficulty.

## D8 — Schedule a perimeter counterexample every third sample (G2)

**Choice.** For `sample_index % 3 == 0`, use component sizes/shapes where size order and perimeter order disagree: a 6-cell 2×3 rectangle has perimeter 10, while a 5-cell staircase has perimeter 12. The intended second-by-size component is the staircase; the rival’s second-by-perimeter component is the rectangle.

**Rationale.** The perimeter rival fits every canonical pair. Randomly hoping to draw a counterexample is not enough for complete lessons. A period-3 schedule means any three consecutive examples contain at least one witness, independent of the starting residue.

**Alternatives rejected.** Purely random witnesses; no lesson-level guarantee. Every sample as a witness; unnecessarily narrows natural shape variation. Hard-coded lesson-start assumptions; brittle under cyclic starts.

**Probe.** Exact counterexample [`checks/question_counterexample.json`](checks/question_counterexample.json); test over every three-consecutive window; 100 lessons per band with all residues 0/1/2 represented 34/33/33.

**Failure modes.** The guarantee applies only to three consecutive sample indices. An external assembler that skips indices can omit the witness.

## D9 — Declare the rival and make lesson identifiability executable (G2)

**Choice.** Add `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `EXAMPLES_NEEDED=3`, and `lesson_identifiable`.

**Rationale.** A prose claim that a generator is educationally sound cannot be checked. The battery and reusable census need callable definitions of both the witness and the strongest known rival.

**Alternative rejected.** Hard-code rival names only inside the stress script. That would let declarations and tests silently drift apart. The probe instead iterates the generator’s actual declarations.

**Probe.** Official `semantic_gate`; stress probe first checks the declared shortcut against every usable canonical pair, then checks every assembled lesson.

**Failure modes.** The contract protects against the declared perimeter rival, not every conceivable wrong rule. New rivals should be added to the declarations and census rather than inferred from the existing result.

## D10 — Strict structural validation (G1)

**Choice.** Validate grid shape/cells, dimensions, exactly one decoration color, one connected decoration component of size 1–3, 3–5 red components, and distinct red sizes. `strict_canonical_like` delegates to this validator.

**Rationale.** The old validator admitted malformed semantic cases and did not make exact controls safely observable. Strong validation lets failures be caught at the generator boundary.

**Alternatives rejected.** Validate only dimensions/palette or trust constructive generation. Direct validator tests deliberately mutate valid grids, so the contract remains useful for future edits and external checks.

**Probe.** Mutation tests, official `selfcheck`, `defect_lint`, and `profile_floor`.

**Failure modes.** As noted in D4, the validator intentionally excludes tied red sizes even though the raw Racket implementation has a tie-breaker.

## D11 — Reusable independent probes, not production self-confirmation (G2)

**Choice.** Put a separate component/perimeter/crop oracle in `workspace/reference_probe.py` and a source-bound lesson census in `workspace/stress_lessons.py`.

**Rationale.** Tests that call only the production helper can repeat the same bug. The independent probe separately derives outputs and records generator hashes, sampler formulas, unique counts, and domain limits.

**Alternative rejected.** A one-off notebook or unretained shell script. Future agents need an executable artifact they can rerun after changes.

**Probe.** `tests/test_stress_lessons.py` and final `checks/lesson_census.json`.

**Failure modes.** Independence is practical, not formal: both implementations are Python and share the same task interpretation. Racket output remains the authority.

## D12 — Synchronize only the redundant Racket text copy (G3)

**Choice.** Replace the active base-solution `target_code` text with the exact unchanged canonical text; do not edit `shared/data/canonical/puzzles.jsonl`.

**Rationale.** `authority_sync` identified two active textual authorities. They were behaviorally equivalent but not byte/text normalized, making provenance ambiguous.

**Alternative rejected.** Change the canonical rule or suppress the checker. Neither addresses provenance cleanly.

**Probe.** Final `authority_sync`, `rule_smoke`, and `racket_lint` all green.

**Failure modes.** Any downstream system that treats the alternate text hash as identity will see a change even though semantics are preserved.
