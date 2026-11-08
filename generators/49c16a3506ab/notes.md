# Working notes: 49c16a3506ab

## Current parametric deliverable

`workspace/parametric/` now contains a separate proposed `stop_short=0|1|2`
family. The default returns the exact canonical Racket source; alternatives
stop one or two cells earlier along the already-computed canonical ray, clipped
at the source. This preserves own-color binding, all three motion branches and
the original edge-termination behavior. Canonical generator/rule bytes remain
unchanged. The production 9..15 manifold remains; only this opt-in sampler
extends to 9..30 with more scatters, central content and longer rays.

The native adapter supports 2..6 demonstrations and 1..4 queries independently.
All settings share input streams; two demos teach both corner orientations.
The four-query schedule includes 30x30. Public batch challenges and single-query
turn projections have visible-byte IDs; private order/settings/answers remain
separate. A one-query request and the first turn of a four-query request match.

Current evidence: 38 focused tests passed; 30/30 native-contract episodes across
all supported demo counts and three settings passed, with 537 Racket evaluations
including 16 boundary scenes and six canonical labels. An independent 160-case
size/orientation probe had no failures (maximum six of 96 placement attempts).
Boolean certificate equality and cached generic adapter imports found in review
are repaired with regressions. See the prototype README for commands and limits.
`evidence/manifest.json` is source inventory, not variant acceptance. Next owner
step: native qualification/acceptance if this family should enter the pool.

## Retained lead

The current source was the selected 3.0.0 baseline described by the retained associated notes, especially the prior rebuild from a lookup-patch generator to a corner-block slide grammar. I treated those notes only as a lead and remeasured the selected bytes. The before battery passed all 12 stages.

## Review finding

A deterministic 600-draw-per-band probe found that every generated scene gave the two colors the same scatter count and the same branch histogram, while two of the three unique canonical profiles used unequal per-color counts and differing histograms. The general battery did not report this coupling. The old 75/25 random corner draw also allowed a four-pair lesson to show only canonical main-diagonal layouts, leaving a plausible `canonical_main_only` rule alive. Rare generated scenes likewise failed to distinguish color ownership from a nearest-block rule.

## Selected repair

Version 3.1.0 adds an exact `scatter_relation` axis (`equal`, `first_sparse`, `second_sparse`), treats `scatter_count` as the dense-color maximum, and keeps all motion branches present for both colors. It alternates `corner_pair` by sample index unless explicitly overridden, adds executable `nearest_anchor` and `canonical_main_only` rivals, and constructively requires a source that is strictly nearer to the other color's block while still moving to its own-color block. Placement uses deterministic bounded MRV restarts; an initial exhaustive witness-pinned search was discarded after a retained task-test timeout exposed exponential behavior. An intermediate semantic-gate run also rejected a non-discriminating `main_diagonal_pair` presence hook; it was removed because the anti-diagonal hook, not a fabricated main-only rival, supplies the meaningful orientation counterexample.

## Limits

The schedule guarantees both orientations in every four consecutive sample indices and the declared-rival tests cover every query rotation of those four pairs. This is finite evidence against named rivals, not a proof of unique induction against every possible hypothesis. The canonical data remain all main-diagonal, so anti-diagonal transfer is taught by generated examples rather than independently confirmed by canonical examples.
## Current reviewer considerations

Source SHA-256: `4f0a0a76b26e3fdff021a7009bf890ddc707265cc0d7b86311b57f9d1696e894`.

# Decisions: 49c16a3506ab

Final generator SHA-256: `4f0a0a76b26e3fdff021a7009bf890ddc707265cc0d7b86311b57f9d1696e894`.

## D1 — Preserve the selected global slide rule

**Decision.** Keep the 3.0.0 task law and Racket authority unchanged: each scattered cell moves toward the solid 3×3 block of its own color, horizontally in the block's row band, vertically in its column band, and diagonally otherwise, stopping adjacent to the block.

**Original rationale.** The retained lead `local-random-29a4c9396363` had already rejected a finite 5×5 lookup-table interpretation and rebuilt the sampler around the canonical global motion grammar. The before battery confirmed the selected bytes remained authority-synchronized.

**Alternatives rejected.** No rule rewrite, new output behavior, or canonical edit was justified. The defects were in sampling and teaching support, not labels.

**Probe.** Rule smoke, authority sync, six canonical rows, task tests, and the fresh solve all use the unchanged `RULE_HASH = b81d150b289c`.

**Limitation.** Canonical examples all use main-diagonal anchors; anti-diagonal behavior remains symmetry-based generated evidence.

## D2 — Treat cross-color equality as a defect, not a harmless simplification

**Decision.** Vary the two colors' scatter counts independently through a declared three-way relation.

**Original rationale.** Unknown. The 3.0.0 implementation reused one `scatter_count` and one branch histogram for both colors, perhaps for construction simplicity, but no task invariant requires equality.

**Measured failure.** In 600 deterministic draws per band, equal count and equal branch-histogram fractions were both 1.0. Two of three unique canonical profiles were asymmetric. Evidence: `checks/scatter-profile-before.json`.

**Alternatives considered.** Fully independent random counts were rejected because the relationship would not be exactly controllable or easily observable. A binary equal/unequal axis was rejected because it would still fix which color is sparse.

**Selected representation.** `scatter_relation = equal|first_sparse|second_sparse`, with `scatter_count` as the dense maximum and sparse count `max(3, dense-2)`.

**Probe.** Exact override tests and `checks/scatter-profile-after.json`.

**Failure modes.** A future change could ignore the relation, make one ordering impossible, or infer the wrong dense maximum. `observe_overrides` and cross-product tests catch all three.

## D3 — Retain every motion branch for each color

**Decision.** Allow per-color totals 3..6, but require at least one row, column, and diagonal source for each color.

**Rationale.** Branch presence directly teaches the task's piecewise motion law. The sparse count bottoms out at three specifically so no branch disappears.

**Alternatives rejected.** Allowing totals 1 or 2 would make branch-complete lessons depend on chance or on the other color. Forcing identical histograms was the baseline defect.

**Probe.** `_branch_counts`, strict self-check, exact relation tests, and final battery semantic/profile stages.

**Limitation.** Generated branch counts are compact templates, not all integer compositions of a total.

## D4 — Schedule corner orientation deterministically

**Decision.** Default sample indices alternate `main` and `anti`; explicit overrides remain exact.

**Original rationale.** The old tuple `("main", "main", "main", "anti")` favored canonical geometry but made complete four-example lessons probabilistically ambiguous.

**Alternatives considered.** Retaining random 75/25 sampling plus lesson rejection was rejected as opaque and potentially expensive. A four-step schedule with three main examples was rejected because some cyclic three-demo subsets still omit anti geometry.

**Probe.** Focused tests enumerate seeds and every four-example start; the 300-lesson census records start residues and refutes `canonical_main_only` in production and all query rotations.

**Potential shortcut.** The schedule depends on hidden sample index, but geometry is visible in every input and the rule does not depend on sequence position.

## D5 — Add `canonical_main_only` as an executable rival

**Decision.** Declare the rule that applies motion only to main-diagonal block pairs and otherwise returns identity.

**Rationale.** It fits all six usable canonical rows, so ordinary canonical correctness cannot refute it. It is the most direct hypothesis created by the canonical geometry restriction.

**Rejected alternative.** A mere orientation-presence statistic would not establish that the differing orientation changes a rival prediction.

**Probe.** Canonical-rival fit is 6/6 in `checks/lesson-census-final.json`; generated lessons refute it 300/300 and rotations 1,500/1,500.

**Limitation.** This is one named extrapolation rival, not exhaustive symmetry reasoning.

## D6 — Force a color-binding counterexample in every ordinary draw

**Decision.** Require at least one scattered source to be strictly nearer to the other color's block than to its own.

**Rationale.** Without such a witness, same-color ownership and nearest-block geometry often agree. The intended rule should be observable from input/output behavior rather than inferred from prose.

**Alternatives considered.** Merely checking that both colors occur was rejected because it does not change the nearest-anchor prediction. Randomly hoping for a witness was rejected because lesson identifiability would remain probabilistic.

**Probe.** `SEMANTIC_WITNESSES["color_binding"]`, the 240-draw focused test, and the live `nearest_anchor` rival in the 300-lesson census.

**Failure modes.** Collision resolution could remove the witness or choose a destination occupied by another source. Placement reserves both source and destination and tests the final grid.

## D7 — Use Chebyshev distance only for constructing the rival witness

**Decision.** Measure distance from a source cell to the nearest cell of each 3×3 block with Chebyshev distance.

**Rationale.** The authoritative motion includes diagonal steps, so Chebyshev distance corresponds to unconstrained step count to a block. It creates a clean “geometrically nearer but semantically wrong color” case.

**Rejected alternatives.** Manhattan distance can disagree with the diagonal motion metric; center-to-center distance ignores block extent.

**Boundary.** Distance never labels data and is not part of the Racket rule. It is used only to construct and score a rival.

## D8 — Replace exhaustive placement with bounded MRV search

**Decision.** Pin one valid color-binding witness, then use deterministic bounded restarts and choose the remaining requirement with the fewest legal candidates.

**Rationale.** The first fixed-order exhaustive implementation became exponential under the expanded override cross-product. The retained timeout is in `checks/tdd-green/result.json`.

**Alternatives considered.** Raising timeouts was rejected because it hides algorithmic fragility. Greedy placement without restart was rejected because rare legal combinations could fail spuriously.

**Probe.** The formerly hanging exact case completes quickly; the final override stage audits the expanded matrix and passes.

**Failure modes.** If all 128 deterministic attempts fail, generation raises loudly rather than returning a malformed scene.

## D9 — Keep the selected geometry and palette bounds

**Decision.** Retain background 6, two distinct non-6 colors, exactly two opposite corner blocks, 3×3 block size, dimensions 9..15, and dense counts 4..6.

**Original rationale.** The associated note `bounded_extrapolation` states that these bounds cover the canonical family while avoiding unsupported block counts and adjacent anchors.

**Alternatives rejected.** Adjacent anchors, more than two blocks, different block sizes, and larger canvases were not supported by canonical evidence and would expand the task rather than repair its curriculum.

**Probe.** Strict profile/self-check stages and canonical-profile floor.

**Limitation.** This is an intentionally bounded training manifold, not the full mathematical domain of the slide rule.

## D10 — Make portable task tests part of the repair

**Decision.** Resolve canonical data and repository roots through `reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`.

**Rationale.** The official task-test stage copies tests into an isolated runtime. Fixed `Path(__file__).parents[...]` assumptions failed before pytest collection, hiding the new red cases.

**Alternatives rejected.** Running pytest only from the source checkout was rejected because it would not test the maintainer's portable intake layout.

**Probe.** `checks/task-tests/result.json` records 892 executed/passed tests in the isolated runtime.

**Failure mode.** Future tests that reintroduce fixed-depth paths are caught by task-test preflight.

## D11 — Keep a source-bound cross-object probe

**Decision.** Add `workspace/probe_scatter_profiles.py`, with deterministic seeds, 600 draws per band in the retained reports, and canonical-profile extraction.

**Rationale.** The general battery was green before and after; a reusable independent probe is needed to make the actual repaired blind spot measurable.

**Alternatives rejected.** A single anecdotal grid or only a unit assertion would not quantify whether coupling remained systemic.

**Probe outputs.** `checks/scatter-profile-before.json` and `checks/scatter-profile-after.json` bind results to exact generator hashes.

**Limitation.** The probe checks only count/histogram coupling, not every possible cross-object dependency.

## D12 — Remove a witness that does not discriminate

**Decision.** Delete the declared `main_diagonal_pair` witness after semantic-gate rejection.

**Rationale.** Presence alone refuted no named rival. Keeping it would inflate witness coverage without teaching evidence.

**Alternative rejected.** Inventing a contrived “anti-only” rival solely to justify the hook was rejected. The meaningful canonical-main-only confusion is already refuted by the anti-diagonal witness.

**Probe.** Intermediate failure: `checks/after-intermediate-weak-witness/checks/49c16a3506ab_after_semantic_gate.json`; final semantic gate green under `checks/after/`.

## D13 — Four demonstrations and arbitrary query holdout

**Decision.** Keep `EXAMPLES_NEEDED = 4` and support holding out any one of the five materialized pairs in the census policy.

**Rationale.** Four consecutive demonstrations guarantee both orientations while retaining broad shape/color/count variation. Downstream assembly may rotate the query, so ordered-only evidence is insufficient.

**Probe.** 300 production lessons, 1,500 unique input/output pairs, and 1,500 rotations with zero ambiguity against declared rivals (`checks/lesson-census-final.json`).

**Limitations.** Rotations reuse each materialized five-pair bundle and do not enumerate every possible program or every cyclic sampler window.

## D14 — Preserve failed iterations and exposure declarations

**Decision.** Retain the expected red suite, the search timeout, the weak-witness rejection, interrupted/resumed after runs, blind solve, and exposed final solve.

**Rationale.** A green final run is stronger when the exact tests are shown detecting absent behavior and weak contracts. The final solve correctly declares prior rule/generator exposure.

**Boundary.** No masked solve labels, token traces, or model accuracy claims are made.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/49c16a3506ab/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
