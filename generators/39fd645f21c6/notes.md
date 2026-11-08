# Working notes: 39fd645f21c6

## Review finding

The selected v3.0.1 baseline taught a narrower rule than its authority: every positive component was an exact shape copy of the blue seed, while decoys differed in area. Thus “recolor exact copies” (and often area-based variants) fit the canonical demonstrations and the generated distribution. Its advertised axes were partly dead, `RULE_HASH` was not pinned, and `self_check` accepted all tested destructive mutations.

No prior return was used as an implementation lead. `evidence/associated_notes.jsonl` was empty; measurements came from the immutable selected baseline and retained before-check evidence.

## v4 design

- Preserve the canonical Racket authority and pin `RULE_HASH = 36a57f0bfc36`.
- Use a static, audited shape bank indexed by `(area, holes, symmetry class)`.
- Place a blue seed, one or two different-shape full-triple matches, and three single-coordinate decoys.
- Cover asymmetric, holed, row-symmetric, column-symmetric, and doubly symmetric target families.
- Use only the three exact canonical dimension/palette profiles.
- Advertise only recoverable exact axes: profile, target family, and match count.
- Reject unknown overrides; test the full legal override product.
- Model the intended rule and eight plausible rivals in executable task-local functions.
- Make each complete three-demo/one-query lesson identifiable for every cyclic query position.

A first cyclic schedule left `first_equal_triple` viable for one rotation. The final schedule alternates match counts and orders target families so each three-example window contains a decisive two-match witness. An intermediate palette allowed input color 8 to hide a disagreement; input palettes now exclude 8 because cyan is the output marker.

## Measurements

- Before battery: 6 green, 2 advisory, 4 failed (`lint`, `selfcheck`, `defect_lint`, `override`).
- Intermediate after battery retained: 9 green, 3 failed (`defect_lint`, `semantic_gate`, `override`).
- Final battery: 12/12 green on generator SHA-256 `8019e41ecb238372519d352afce1e60b7de712adc3d589b611197f6f05b79ab8`.
- Selected task tests: 40 passed.
- Source-bound lesson census: 300 lessons, 100 per band, 1,200 unique inputs, no declared ambiguity.
- Independent shortcut probe: 300 lessons and all 1,200 cyclic query rotations, zero failures; every declared rival has a materialized counterexample.

## Limits

The shape vocabulary and declared rival family are finite. These checks establish identifiability against the modeled shortcuts, not universal human or model induction. Difficulty changes deterministic placement/palette randomness but not semantic rule depth; all bands intentionally share the same curriculum guarantees.
## Current reviewer considerations

Source SHA-256: `8019e41ecb238372519d352afce1e60b7de712adc3d589b611197f6f05b79ab8`.

# Design decisions for 39fd645f21c6

No prior return was used as a lead. The selected v3.0.1 source was the baseline, and `evidence/associated_notes.jsonl` was empty.

## D1 — Keep the canonical Racket rule unchanged

**Choice.** Preserve the canonical transformation and pin `RULE_HASH = "36a57f0bfc36"` in the generator.

**Rationale.** Rule smoke and authority sync already passed on the baseline. The defect was pedagogical: the input distribution made a narrower exact-shape rule sufficient. Changing a correct authority would add risk without fixing the teaching problem.

**Alternatives rejected.** Reinterpreting the rule as exact-shape matching would match the old distribution but contradict the canonical feature-triple authority. Rewriting Racket to mirror Python would also create unnecessary dual-authority churn.

**Probe.** Final `rule_smoke`, `racket_lint`, and `authority_sync` are green in `checks/after-v2/`; the exact shortcut counterexample receipt records rule hash `36a57f0bfc36`.

**Limit.** This review establishes source/hash continuity, not catalog approval.

## D2 — Restrict scene profiles to exact canonical size/palette profiles

**Choice.** Use only `11x16` with five colors, `12x16` with five colors, and `12x17` with five colors.

**Rationale.** These are the canonical profiles and satisfy the profile floor without adding unrelated scale variation. All three are observable directly from the returned input, so `scene_profile` is an honest exact override.

**Alternatives rejected.** The baseline's broad approximate dimensions increased texture without contributing semantic evidence. Advertising height and width as independent axes would imply joint combinations the layout and canonical profile contract do not support.

**Probe.** The final override product, strict-profile gate, and profile-floor stage all pass.

**Failure mode / limit.** The distribution does not test scale generalization outside canonical dimensions.

## D3 — Use five target feature families

**Choice.** Include seed triples representing asymmetric/no-hole, asymmetric/one-hole, row-symmetric, column-symmetric, and both-axis-symmetric components.

**Rationale.** A single asymmetric family cannot make the symmetry coordinate meaningful. Five families exercise all four symmetry classes and both observed hole counts while staying within compact canonical grids.

**Alternatives rejected.** Random shape enumeration was rejected because rejection sampling could silently bias or omit rare triples. A single canonical-looking family was rejected as too narrow.

**Probe.** Static-bank tests verify each shape's measured triple, and semantic witnesses cover every `target_family` override.

**Failure mode / limit.** The bank is finite and covers holes 0–1, not arbitrary topology.

## D4 — Make every positive a different-shape feature twin

**Choice.** The blue seed and every positive candidate share the full feature triple but have different translation-normalized shapes.

**Rationale.** Exact-shape matching is the strongest canonical shortcut: it fits all three canonical demonstrations. A positive different-shape twin is the direct counterexample.

**Alternatives rejected.** Mixing exact copies and feature twins would preserve unnecessary shortcut support in some scenes. Merely adding more decoys would not falsify exact-shape matching.

**Probe.** `test_generated_matches_are_different_shapes`, the exact counterexample in `checks/shortcut-counterexample/`, and the independent probe all pass.

**Failure mode / limit.** Shape equivalence is translation-normalized only; rotation/reflection are not treated as exact copies unless their measured triple also matches.

## D5 — Add three one-coordinate decoys to every scene

**Choice.** Add one decoy differing only in area, one only in hole count, and one only in symmetry class.

**Rationale.** These are minimal contrasts for the conjunction `(area, holes, symmetry)`. They refute single-coordinate and pairwise-coordinate rivals while keeping the intended positive relation constant.

**Alternatives rejected.** Decoys differing in several coordinates are easier to separate and do not identify which features matter. Random decoys can accidentally leave a rival viable.

**Probe.** `semantic_observables` reports all three decoy types; task tests assert each differs in exactly one coordinate; the census refutes area-only, holes-only, symmetry-only, and all three pairwise rivals in every sampled lesson.

**Failure mode / limit.** The rival list is explicit and finite; an undeclared exotic heuristic may still exist.

## D6 — Alternate one- and two-match scenes

**Choice.** `match_count` is exactly 1 or 2, scheduled alternately, and recoverable from the input.

**Rationale.** A two-match scene is required to refute “recolor only the first equal-triple object.” One-match scenes retain the canonical visual density and prevent every query from having the same answer cardinality.

**Alternatives rejected.** Always one match leaves the first-match rival viable. Always two matches reduces variation and departs farther from canonical demonstrations.

**Probe.** A new cyclic-rotation test initially failed because one window left `first_equal_triple` viable; the revised six-step schedule passes 40 tests and all 1,200 query rotations.

**Failure mode / limit.** At most two positives are emitted because six compact components already fill the canonical profiles cleanly.

## D7 — Use a deterministic six-step curriculum schedule

**Choice.** Profiles, target families, and match counts follow a period-six schedule, with keyed randomness only for shape selection, palette, and legal placement.

**Rationale.** Any consecutive four scenes become a three-demo/one-query lesson. A small deterministic period makes it affordable to prove every cyclic start has the required witnesses rather than relying on marginal frequency.

**Alternatives rejected.** Independent random axis draws can produce a complete lesson with no two-match witness or no decisive feature contrast even when aggregate frequencies look healthy.

**Probe.** The source-bound census covers consecutive starts and the task-local probe rotates every one of 300 four-pair lessons through all query positions.

**Failure mode / limit.** Deterministic schedules can be learned as sequence texture if sample indices are exposed; the puzzle inputs themselves contain no index marker.

## D8 — Exclude cyan 8 from input palettes

**Choice.** Use color 8 only as the output marker, never as an ordinary input component color.

**Rationale.** An intermediate implementation allowed 8 in input palettes. On some examples, a rival's failure to recolor was visually hidden because the object was already cyan. Excluding 8 makes every positive recoloring observable.

**Alternatives rejected.** Allowing 8 with special-case role constraints was more complex and still made counterexample reasoning brittle.

**Probe.** The retained intermediate failure is in `checks/after-final/`; final semantic and task tests assert `input_contains_cyan == false`.

**Failure mode / limit.** This intentionally narrows input palette identity, though palette size remains canonical and nonsemantic colors still vary.

## D9 — Advertise only three exact, observable overrides

**Choice.** `AXES` contains `scene_profile`, `target_family`, and `match_count`. Unknown overrides raise `ValueError`, and `observe_overrides` recovers all three.

**Rationale.** The baseline advertised controls that were dead, sampled indirectly, or not observable. The replacement contract favors a small exact surface over decorative knobs.

**Alternatives rejected.** Exposing raw shape index, palette, or placement would enlarge the override product without serving rule identification. Keeping deprecated axes would preserve misleading API promises.

**Probe.** All 30 legal override combinations pass generation, observation, and self-check; unknown override rejection passes; final override gate is green.

**Failure mode / limit.** Palette and placement remain deterministic keyed texture, not caller-controlled axes.

## D10 — Separate broad canonical validity from strong teaching witnesses

**Choice.** `self_check` / `strict_canonical_like` accept lawful canonical examples and generated scenes. Stronger properties—different-shape twins, one-coordinate decoys, and lesson-level rival refutation—are exposed through semantic observables, witnesses, and `lesson_identifiable`.

**Rationale.** Requiring every canonical input to contain v4's new anti-shortcut witnesses would incorrectly reject the authority's own demonstrations. Conversely, validation alone cannot establish that a complete lesson teaches the full rule.

**Alternatives rejected.** A single overstrict validator caused the intermediate semantic gate to reject canonical examples. A permissive validator with no semantic hooks recreated the baseline's acceptance-only self-check.

**Probe.** Canonical support, mutation rejection, semantic witness coverage, and lesson identifiability all have separate tests and all final battery stages pass.

**Failure mode / limit.** A grid may be lawful but pedagogically weak in isolation; lesson assembly is responsible for curriculum strength.

## D11 — Treat difficulty as deterministic texture, not a different rule

**Choice.** Difficulty participates in keyed RNG streams for palette/placement while the same semantic schedule and exact profiles remain available in every band.

**Rationale.** ARC rule depth should not change across bands, and the required 100-lessons-per-band census should test the same contract under distinct deterministic draws.

**Alternatives rejected.** Making hard examples larger would violate exact canonical profiles; removing difficulty from randomness made all three bands byte-identical for the same seed/sample.

**Probe.** Distribution tests verify band determinism and nonidentity; the census materialized 100 lessons and 400 unique inputs in each band.

**Failure mode / limit.** Difficulty does not currently encode a meaningful increase in cognitive complexity.

## Current native parametric build — 2026-10-25

Built a source-bound `match_policy` family without changing the approved production generator or canonical authority. `exact_triple` returns the selected canonical Racket source exactly; `best_partial` computes each candidate's Hamming mismatch against the blue seed over `(area, hole count, symmetry class)`, finds the input-dependent global minimum, and recolors every candidate attaining it.

The family supports independently requested 2–6 demonstrations and 1–4 queries while always storing four distinct queries. The retained curriculum reaches 14×17, 18×21, 24×27, and 30×30; the largest case contains 13 components and 106 foreground cells. Demonstrations include both no-exact-match scenes with multiple one-coordinate winners and an exact-match scene that forces minimum mismatch zero. Sequential public projection exposes one query input per turn and is prefix-stable with single-query generation.

A bounded protected-Racket audit covered 12 episodes across both settings, seeds 0/17, and demonstration counts 2/3/6: 92 label claims, 41 distinct Racket executions, 16 saved public turns, nine executable rivals, and zero findings. Native qualification passed both settings on both qualification seeds with three demonstrations, four queries, and 40 protected-Racket evaluations. The retained wrong-minimum witness changes the qualified 30×30 output and was replayed through protected Racket.

The final staged task suite's portability preflight flagged legacy imports from `scripts` and `src.core`. The test now reads canonical pairs and rule authority through `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`. Final task result: 69 passed with no portability warning.

Limits: the shape vocabulary and adversarial family remain finite and do not prove universal identifiability. Owner exact-source integration, fresh native qualification/witness replay, and explicit acceptance remain pending; no training admission is claimed.
