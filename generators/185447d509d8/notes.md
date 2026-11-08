# Working notes: 185447d509d8

## Current rule and domain

Find exactly four isolated, differently coloured 4-connected tetrominoes. Order them by the row-major positions of their bounding boxes. Output a 4×4 matrix with red (`2`) at `[i][j]` exactly when objects `i` and `j` are equivalent under any of the eight D4 rotations/reflections; otherwise output black (`0`). Canonical rule hash: `9586787e3555`.

Generator version `3.1.0` exposes two exact, pixel-observable controls:

- `size_profile`: `12x14|13x15|12x16|14x14|12x15`;
- `partition`: `one_pair|two_pairs`.

Ordinary inputs always include a reflection-only S/Z pair, an orientation-variant equivalent pair, and equal-area non-equivalent objects. These witness and refute the declared rotations-only, exact-orientation-only, and same-area rivals.

## Reversed prior choices

Version 2.2.0 sampled 2–5 objects, used opportunistic placement, advertised several ignored or stale controls, and offered `partition=all_same` even though `self_check` rejected the resulting contrast-free input. Its summary still described three objects and a 3×3 matrix. Version 3.1.0 instead guarantees four complete objects through separated constructive zones, removes dishonest/contrast-poor controls, pins `RULE_HASH`, and validates exact overrides by observing returned pixels. Evidence: retained prior reproduction under `counterexamples/review-d19682319424723a-v0002/`, final tests under `tests/`, and source-bound check reports under the review return’s `checks/` directory.

The first 3.1.0 draft also left difficulty behavior byte-identical. The final schedule makes difficulty visible: easy uses smaller one-pair profiles, medium uses two profiles and both partitions, and hard uses `12x16` with two pairs. Explicit valid overrides remain available in every band.

## Known limits

- The curriculum intentionally covers tetrominoes only, fixed arity four, and relation partitions `[1,1,2]` or `[2,2]`; the canonical rule itself is more general.
- The generated output codomain is exactly nine labelled matrices.
- Finite named-rival checks and a 300-lesson/1,200-rotation census do not prove unique induction against every possible rule.
- Difficulty changes visible profile/relational density, not the underlying law, and has not been calibrated against model accuracy.

## Open findings

No blocking task-local finding remains in this review. Future work could expand shape areas or arities only if equally strong per-lesson witnesses and observable contracts are retained.
## Current reviewer considerations

Source SHA-256: `f64540d7798e08e16bc7a4fd0ea90a6e572755e3050aac5fb5c2257368e703a3`.

# Decisions for `185447d509d8`

Final generator SHA-256: `f64540d7798e08e16bc7a4fd0ea90a6e572755e3050aac5fb5c2257368e703a3`.

## D1 (R1): preserve the canonical authority

- **Prior choice:** imported generator version 2.2.0 had no pinned `RULE_HASH` even though its intended transformation matched the canonical task.
- **New choice:** declare `RULE_HASH = "9586787e3555"` and leave the canonical Racket implementation unchanged.
- **Rationale:** the defect was in generation and teaching support, not in the reference transformation.
- **Alternatives rejected:** rewriting the Racket rule or adding a Python label oracle as authority. Either would introduce unnecessary authority drift.
- **Probe/evidence:** canonical-pair task test, final rule smoke, Racket lint, and authority-sync stages in `checks/after/`.
- **Failure mode / limit:** the Python test oracle is only an independent regression aid; canonical Racket remains authoritative.

## D2 (R1): exactly four complete objects

- **Prior choice:** sample 2–5 requested objects and place opportunistically; failed placements could silently reduce the realized count while stale metadata still claimed exactly three.
- **New choice:** always generate four differently coloured tetrominoes and constructively place one in each of four separated zones.
- **Rationale:** the canonical examples use four objects and a 4×4 relation matrix; fixed arity makes ordering and output shape explicit while eliminating silent object loss.
- **Alternatives considered:** retain variable arity with rejection sampling; use a general packing solver; keep three objects to match stale prose. Rejection/packing add complexity without improving this lesson, and three objects contradict the canonical support.
- **Probe/evidence:** `test_normal_draws_have_four_complete_objects_and_pass_self_check`; 96 ordinary draws across four difficulty values; final self-check/distribution gates.
- **Failure mode / limit:** this generator no longer trains variable relation-matrix sizes. That is an intentional curriculum restriction, not a change to the canonical rule.

## D3 (R1): expose only observable controls

- **Prior choice:** advertise controls such as palette kind/size, distinct-colour count, density, stale position labels, and `partition=all_same` even when controls were ignored, fixed, mislabeled, or validator-incompatible.
- **New choice:** expose only `size_profile` and `partition`, with exact finite string domains recoverable by `observe_overrides()`.
- **Rationale:** an exact control should alter returned pixels and be mechanically verifiable. Invalid/unknown/wrongly typed values now fail loudly.
- **Alternatives considered:** make every old axis real; keep hidden implementation knobs; mark contradictory combinations incompatible. The old axes did not add useful semantic coverage, and `all_same` cannot teach contrast within a lesson.
- **Probe/evidence:** `test_every_advertised_override_is_observable_and_honored`, invalid-control parameter tests, and final override gate.
- **Failure mode / limit:** palette and position remain randomized but are not exact public axes.

## D4 (R2): use one-pair and two-pair relation structures

- **Prior choice:** advertise all-distinct, one-pair, and all-same structures, while `self_check` rejected all-same and the normal generator used a wider, inconsistent object-count regime.
- **New choice:** four objects with either one pair plus two singletons (`[1,1,2]`) or two pairs (`[2,2]`).
- **Rationale:** both structures include positive and negative off-diagonal relations. They yield nine distinct labelled matrices and avoid trivial identity/full matrices.
- **Alternatives considered:** all-distinct, all-same, triplet-plus-singleton, or unrestricted partitions. All-distinct/all-same are contrast-poor; triplets would weaken the guaranteed chiral-pair construction without adding a needed rule distinction.
- **Probe/evidence:** exact-codomain test reaches all nine outputs; final distribution/grammar/semantic gates.
- **Failure mode / limit:** the curriculum does not cover every set partition of four objects.

## D5 (R2): force three semantic witnesses in every input

- **Prior choice:** random shapes could accidentally permit rotations-only, exact-orientation-only, or same-area explanations.
- **New choice:** include a randomly rotated S shape and a randomly rotated mirrored S/Z mate; use only area-four shapes from multiple D4 classes; orient equivalent mates differently.
- **Rationale:** a single labelled pair can visibly distinguish reflections from rotations, area from shape class, and orientation equality from D4 equivalence.
- **Alternatives considered:** rely on multi-example probability, resample after weak lessons, or add many ad hoc rival hooks. Constructive witnesses are cheaper and deterministic.
- **Probe/evidence:** all witness and rival assertions in `test_each_generated_input_refutes_declared_shortcuts`; semantic gate; 300-lesson/1,200-rotation census.
- **Failure mode / limit:** the three rivals are plausible but finite. No claim is made that they span all shortcuts.

## D6 (R2): visible difficulty scheduling

- **Prior choice during the first rewrite:** difficulty was accepted but did not affect bytes; the defect linter correctly reported dead bands.
- **New choice:** easy → smaller one-pair profiles, medium → two medium profiles and both partitions, hard → largest-width profile with two pairs. Exact overrides use the full domain at every band.
- **Rationale:** difficulty must be observably non-dead while keeping one rule and avoiding arbitrary changes in colours or semantics.
- **Alternatives considered:** remove difficulty, vary only RNG seeds, increase object count/area by band. The framework expects bands; seed-only variation is not a band effect; changing arity would complicate the output grammar.
- **Probe/evidence:** `checks/tdd-red-difficulty/pytest.txt` followed by `test_difficulty_bands_schedule_distinct_visible_profiles`; final defect lint and profile-floor gates.
- **Failure mode / limit:** “hard” means denser relation structure and a larger canvas, not a measured model-difficulty guarantee.

## D7 (R2): declare the finite output codomain

- **Prior choice:** no explicit grammar-size contract.
- **New choice:** `EXPECTED_OUTPUT_CODOMAIN = 9`.
- **Rationale:** with four labelled positions, one-pair partitions produce `C(4,2)=6` matrices and two-pair perfect matchings produce three.
- **Alternatives considered:** avoid the declaration or expand partitions solely to satisfy a generic diversity heuristic. The finite grammar is intrinsic and useful documentation.
- **Probe/evidence:** `checks/tdd-red-codomain/pytest.txt` and the passing 400-draw reachability test.
- **Failure mode / limit:** nine is the codomain of this repaired generator domain, not of the unconstrained canonical rule.

## D8: retain failures and resume source-bound checks

- **Choice:** keep the partial before battery, red TDD runs, initial after lint failure, and interrupted foreground battery attempts; resume only when the controller verified unchanged source/settings/checkpoint hashes.
- **Rationale:** failed evidence is diagnostically useful, while rerunning everything would obscure which source each result measured.
- **Evidence:** `checks/before/`, `checks/before-defect_lint/`, `checks/tdd-red-*`, `checks/lint/`, and final `checks/after/result.json` with `resumed: true`.
- **Limit:** the outer execution environment imposed a short foreground-shell cap; this is process feedback, not a generator failure.

## Lesson assembly and limits

The production sampler forms lessons with three demonstrations and one query. The wider census sampled 100 lessons per band using deterministic SHA-derived seeds and consecutive requested starts. Query-rotation verification held each materialized pair out once and preserved the remaining order. All 300 production lessons and all 1,200 rotated queries distinguished every declared rival, but the check does not enumerate all random seeds, all cyclic windows, or undeclared hypotheses.
