# Working notes: 9af68e46cf69

## Current opt-in parametric family

`workspace/parametric/adapter.py` adds episode-fixed
`selection=all_enclosed|largest_enclosed_region`. The default is the exact
canonical program. The alternative measures every complete four-connected
background region strictly inside each object's bbox, scores each object by
its largest individual enclosed-region area, and recolors every object tied
for the largest positive score. This preserves topology and whole-object
recoloring while adding a comparison dependent on the inferred region structure.

The mandatory two-demo teaching core distinguishes a single area-four hole from
two area-three holes, then presents tied unit holes with a diagonal background
connection. It teaches maximum versus total area, unit holes, four-connectivity
and all ties, with irregular positives and open-bbox negative decoys. Input RNG
streams remain independent of the hidden setting and requested query count.
The default episode has three demos and four distinct queries; supported counts
are 2–6 and 1–4 independently. Large queries use actual distributed geometry,
including 30×30 content, rather than the production compact fallback.

The native adapter's explicit domain requires 2–3 positive and 1–4 negative
objects with disjoint bboxes and both geometric witnesses. This is separate from
the base validator's count/palette checks; the latter alone does not enforce the
two witness predicates. The prototype's teaching certificate fits competitors
on demonstrations only and does not use private query labels to select them.

Reusable `verify.py` checks exact Racket labels, exports and causal witnesses.
Current source-bound evidence belongs in `workspace/parametric/evidence/current/`
and its native inventory. `largest_total.rkt` is a private wrong-intermediate
counterfactual, not an extra exported setting. Owner integration followed by
fresh native qualification/acceptance remains required; this family makes no
training-admission or universal-identifiability claim. See the task-local README
for exact commands and the finite scope.

Current reviewer checks: 133 task-local pytest tests passed; the reusable verifier
passed 12 episodes, 92 label occurrences, 45 distinct protected-Racket evaluations
(including five canonical pairs), and 48 one-query public exports. Native
qualification passed both settings across seeds 0 and 17 with three demos and
four queries. The source-bound causal witness contains two executed maximum-
versus-sum cases, including a tie. A bounded independent review found no defect
across nine additional seeds and exercised all four negative-object counts.
Sampling remains a small constructive family with translations/reflections;
query winners are untied, while demos and the causal witness cover ties.
Next owner action: integrate the delta, freshly qualify the exact integrated
source, and run native acceptance. Reviewer readiness does not perform that step.

## Intended rule

On a color-9 background, split color-1 pixels into 4-connected objects. Recolor
one whole object to color 8 iff a complete 4-connected color-9 region lies
strictly inside that object's bounding box. A background cell merely appearing
inside the box is insufficient when its region remains connected to the outside.

## Review repair (version 3.0.0)

The imported 2.0.1 generator advertised nine controls that were not reliably
recoverable from pixels, accepted negative textures (`all_holey`, `all_solid`,
`no_objects`) as ordinary draws, allowed trivial inputs through `self_check`,
and generated mostly rectangular positives with no semantic lesson contract.
The repair replaced that API with four exact pixel-recoverable controls:
`grid_h` 9–30, `grid_w` 11–30, `n_holey` 1–3, and `n_solid` 1–4. Unknown and
retired controls are rejected; booleans, floats, numeric strings, invalid bands,
and negative sample indices are rejected rather than coerced.

Every advertised endpoint and pairwise combination is constructive. A compact
9×11 scaffold proves feasibility for the densest request (3 hole-bearing plus 4
no-hole objects); larger/roomier draws try a varied dihedral shape catalogue
under a hard search budget and fall back to that scaffold. The search budget
must propagate out of every DFS frame; an earlier local-only cap caused the
matrix checker to run far beyond its intended bound.

## Teaching contract

Three demonstrations are used (`EXAMPLES_NEEDED = 3`). Every generated input
contains both:

- `irregular_hole`: a true positive that is not a rectangular outline, refuting
  `rectangular_frames_only`;
- `open_bbox_decoy`: a no-hole object whose bbox contains background connected
  to the exterior, refuting `any_bbox_background`.

`SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`,
`LESSON_COMPETITORS`, and `lesson_identifiable` expose this contract to shared
checks. Minimal live reproducers are retained under `counterexamples/`, and
`workspace/probe_contract.py` rechecks canonical labels plus every declared
witness/rival against the selected source.

## Authority decision

The selected `racket_target.target_code` was formatting-synchronized to the
canonical `program_solution`. The archival `raw_code` was intentionally
preserved. Execution semantics did not change: all three forms solved all four
canonical train pairs and the canonical test pair before synchronization.

## Measured final evidence

Generator SHA-256:
`2eb732c96e68ad6de3d40e0af4bf307fcc8f94d0d0774b818adf361814a213a8`.
The final battery is all-green across 12 stages. The override matrix accepted
5,220/5,220 draws across 58 cases and three bands. The semantic smoke test
accepted 600/600 strict samples, found both witnesses and both rival
refutations in every band, identified all 12 production lessons, and found 0/48
ambiguous query rotations. The larger census materialized 300 lessons (1,200
pairs; 1,148 unique inputs) and found 0/300 production ambiguities and 0/1,200
rotation ambiguities. The task-local probe found both witnesses and both rival
disagreements in 36/36 sampled inputs and matched all five labeled canonical
pairs.

## Known limits

The declared rival set is finite; passing it does not prove identifiability
against every possible hypothesis. Shape richness is internal rather than an
exact public axis. The compact fallback deliberately reuses a small constructive
basis on crowded canvases, while default broad draws provide additional shapes
and transformations. No color-role permutations are claimed: colors 9, 1, and 8
are semantically fixed by the authoritative task.
## Current reviewer considerations

Source SHA-256: `2eb732c96e68ad6de3d40e0af4bf307fcc8f94d0d0774b818adf361814a213a8`.

# Decisions: 9af68e46cf69

## D1 — Preserve the authoritative transformation

**Decision.** Keep the enclosure rule unchanged. Synchronize only the selected `target_code` formatting to canonical `program_solution`, and preserve archival `raw_code`.

**Rationale.** Canonical train/test execution already agreed across all sources. The defect was generator truthfulness and pedagogy, not rule correctness.

**Rejected alternative.** Rewriting the Racket algorithm for style or speed would introduce unnecessary semantic risk and erase useful archival provenance.

**Probe and failure mode.** Authority sync and rule smoke execute all five canonical pairs. The final authority report is `checks/after-final/checks/9af68e46cf69_after_authority_sync.json`; normalized hashes agree and execution parity is PASS.

## D2 — Expose only pixel-recoverable exact controls

**Decision.** The public `AXES` are exactly `grid_h` 9–30, `grid_w` 11–30, `n_holey` 1–3, and `n_solid` 1–4.

**Rationale.** Each value is directly recoverable from the generated grid and has a clear exact contract. The 9×11 lower bound supports the densest advertised request; 30×30 is the ARC canvas limit.

**Rejected alternatives.** The old `frame_size_kind`, `solid_shape_kind`, `texture`, `position_bias`, and `inter_object_padding` controls were removed rather than renamed. Their observed pixels did not uniquely establish the requested setting, and negative texture values could delete the lesson.

**Probe and failure mode.** The final override matrix probes endpoints and pairwise combinations across all three bands. It accepts 5,220/5,220 draws over 58 cases with zero findings; `observe_overrides` proves exact recovery. Unknown keys and bool/float/string impostors are explicitly tested and rejected.

## D3 — Make every individual input semantically informative

**Decision.** Every input must include an irregular true-hole positive and an open-bbox no-hole decoy.

**Rationale.** These two witnesses directly distinguish the authoritative rule from the strongest observed cheap shortcuts: “only rectangular frames get recolored” and “any background pixel inside a bounding box implies a hole.” Requiring them per input is stronger and simpler than hoping a multi-example lesson eventually contains them.

**Rejected alternatives.** Randomly sprinkling witness cases at low frequency leaves many lessons ambiguous. Allowing `all_holey`, `all_solid`, or `no_objects` as ordinary modes creates examples with no contrast and was therefore removed.

**Probe and failure mode.** Both witnesses fire and both rivals disagree in 600/600 semantic-gate samples and 36/36 task-local probe samples. Minimal source-bound reproducers are retained in `counterexamples/`.

## D4 — Use three demonstrations and require query-rotation identifiability

**Decision.** Set `EXAMPLES_NEEDED = 3`; assemble three demonstrations plus one query; require `lesson_identifiable` to hold for the production query and every possible query rotation.

**Rationale.** Three demonstrations are enough for the two declared task-specific rivals once every input carries both witnesses. Rotation checking prevents ordering from accidentally making the only disambiguating pair the query.

**Rejected alternatives.** One or two demonstrations save tokens but provide little protection against unmodeled shortcuts. Ordered-only checking was rejected because downstream data assembly may reorder pairs and because the extra four-way test is cheap.

**Probe and failure mode.** The semantic smoke test identifies 12/12 production lessons and 48/48 rotations. The 300-lesson census identifies 300/300 production lessons and 1,200/1,200 rotations. The policy is `require`, not merely diagnostic.

## D5 — Prefer constructive feasibility over unbounded placement retries

**Decision.** Use a varied placement search under a hard node budget, with budget exhaustion propagated through every recursive frame; fall back to a compact constructive scaffold for crowded exact requests.

**Rationale.** Exact axes need total behavior at their advertised endpoints. The scaffold proves feasibility on 9×11 for 3 hole-bearing plus 4 no-hole components, while broad default draws still use richer dihedral shapes.

**Rejected alternatives.** Expanding the minimum canvas would avoid packing difficulty but would break canonical profile support. Unlimited rejection sampling or a local-only DFS cap caused long stalls and made the override checker unreliable.

**Probe and failure mode.** The override matrix completes with no generation errors. Tests explicitly exercise the minimum-canvas maximum-count case and ensure the search budget abort propagates.

## D6 — Weight defaults toward canonical profiles without narrowing exact support

**Decision.** Default draws are canonical-size/palette weighted, but exact dimensions remain available throughout 9–30 by 11–30 in every band.

**Rationale.** The original hard band had zero exact canonical-profile support. Weighting improves fidelity while retaining broad canvas diversity and exact boundary coverage.

**Rejected alternatives.** Sampling uniformly over all dimensions diluted canonical-like examples. Restricting each difficulty to disjoint dimension ranges made declared endpoints false in some bands and caused override rejections.

**Probe and failure mode.** Before: 4/60 exact, 19/60 envelope, hard band zero exact. After: 10/60 exact, 23/60 envelope, with exact support in easy/medium/hard and all 5 canonical inputs accepted.

## D7 — Make validation strict rather than coercive

**Decision.** Accept only literal integers for seeds, indices, and integer axes (excluding booleans); accept only the closed difficulty enum; reject unknown or retired controls.

**Rationale.** Silent coercion destroys reproducibility and allows malformed metadata to appear valid. The before defect lint found 113 strict-scalar problems and an accepted unknown key.

**Rejected alternative.** Coercing numeric strings/floats is convenient at call sites but makes replay receipts and exact override claims ambiguous.

**Probe and failure mode.** Focused tests cover booleans, integral/nonintegral floats, strings, negative indices, invalid bands, and unknown keys. Final defect lint is green.

## D8 — Treat `self_check` as a semantic invariant

**Decision.** `self_check` verifies dimensions, palette, exact component counts, authoritative input/output relation, and the mandatory witness structure; `strict_canonical_like` aliases that strict contract.

**Rationale.** The previous validator accepted tiny unrelated shapes and therefore could not protect the training distribution.

**Rejected alternative.** A shape-agnostic “valid colors and at least one object” check is too weak for an assigned repair and cannot distinguish target examples from impostors.

**Probe and failure mode.** Mutation/impostor tests fail before implementation and pass after; final defect lint reports no blocking self-check weakness.

## D9 — Retain executable rivals and portable evidence

**Decision.** Declare `SEMANTIC_WITNESSES`, `SEMANTIC_RIVALS`, `WITNESS_RIVALS`, `LESSON_COMPETITORS`, and `lesson_identifiable`; add a portable probe plus minimal JSON counterexamples.

**Rationale.** Future agents need machine-checkable contracts, not prose claims. Deriving declarations dynamically in the probe avoids duplicating names and makes drift visible.

**Rejected alternative.** Static screenshots or large copied logs are hard to replay and do not bind to selected source bytes.

**Probe and failure mode.** `workspace/probe_contract.py` records the selected SHA, canonical parity, witness hits, and rival disagreements. Its artifact existence and behavior are covered by task tests.

## Limitations carried forward

- The rival family is finite; no finite gate establishes unique induction against every imaginable hypothesis.
- Shape catalogue choice is internal, not an exact user control.
- Crowded canvases intentionally reuse a compact constructive family.
- Colors 9, 1, and 8 are fixed semantic roles; no palette-permutation claim is made.
- The review measures generated data quality and lesson identifiability, not downstream Qwen3.5-9B accuracy.

<!-- arcpuzzles-current-supplementary:start -->
## Current supplementary checks

Current source-bound ticket observations: `generators/9af68e46cf69/evidence/supplementary-current.json`. Results are reviewer-reported; blocked or unknown stays explicit. These observations do not approve a generator or variant, resolve audits, or admit data to training.
<!-- arcpuzzles-current-supplementary:end -->
