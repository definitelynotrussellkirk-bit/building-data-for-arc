# Working notes: 10bc62b2de84

## Current intended rule

Use color 0 as background. Extract all nonzero 4-connected objects, sort their bounding boxes by left column, crop each object to its bounding box, concatenate crops left-to-right with one zero column between adjacent crops, and bottom-align every crop in an output whose height is the maximum crop height. The selected canonical Racket authority is unchanged and pinned by `RULE_HASH = "eb9f505d4c6b"`.

## Baseline findings and reversals

- Prior sampler: ad hoc random retries; exact axes were not routed through keyed provenance; invalid scalar/unknown overrides were accepted; failed object placements could be silently dropped. Before evidence: `checks/before/`.
- New sampler: exact call validation, strict keyed draws, finite backtracking placement, and a compact fallback. Returned grids always expose the requested `grid_h`, `grid_w`, and `n_objects` or fail loudly.
- Prior distribution: 0/60 exact canonical-profile hits and no semantic contract.
- New distribution: three canonical dimension/palette anchors plus a broad difficulty-scaled profile; every ordinary draw has unequal crop heights.
- Intermediate choice reversed: I briefly declared `LESSON_SCHEDULE_PERIOD = 4`. The semantic gate correctly warned that the period had not been exhaustively enumerated, so I removed the declaration rather than imply evidence that was not run. The deterministic `schedule_profile` remains, but no exhaustive-period claim is made. Evidence: `checks/semantic-first/` and `checks/semantic-second/`.

## Strongest canonical shortcut

All four canonical labelled pairs contain equal-height crops, so top alignment fits every canonical output. Retained exact witness: `counterexamples/top_aligned_shortcut.json`. The generator declares `top_aligned` in semantic/canonical/lesson rival maps and emits unequal-height cases by construction.

## Current distribution and assumptions

- Canvas: 6–14 rows, 9–22 columns.
- Objects: 2–6 nonzero 4-connected, monochrome, distinct-color objects; each has 2–7 cells.
- Objects do not overlap or touch orthogonally; left bbox columns are unique.
- Rich normalized shapes are attempted first; a compact family is the deterministic constructive fallback.
- `strict_canonical_like` accepts lawful equal-height canonical data. Unequal heights are a teaching guarantee of ordinary generation, not a universal validity requirement.
- `EXAMPLES_NEEDED = 3`; production lesson shape is three ordered demonstrations plus one query.

## Final measured evidence

Final generator SHA-256: `5c1afcc5dcdc13ab461d1e327cf2ff8decb4300c0af524bf96f73f9ad2818756`.

- Full after battery: 12/12 green (`checks/after/`).
- Portable task tests: 44/44 pass (`checks/task-tests/`).
- Exact override matrix: 24,480/24,480 accepted, zero findings.
- Integer-axis construction: all 630 combinations pass.
- Semantic sample: 600/600 lawful and unequal-height; declared rival checks 60/60; 12/12 smoke lessons clear; 0/48 diagnostic rotations ambiguous.
- Large census: 300/300 lessons, 1,200 pairs, 1,200 rotations, 1,200 unique inputs; zero production/rotation ambiguity or scoring/materialization errors (`checks/lesson-census.json`).
- Post-repair visible-only solve was prepared from this exact hash and passed all three visible examples on revision 1; earlier rule exposure is recorded honestly (`solve/summary.json`).

## Known limits / open findings

- Evidence is finite and covers the declared `top_aligned` rival, not every possible hypothesis.
- The sampler is intentionally narrower than the complete executable Racket domain: finite shape bank, distinct colors, no touching, unique left edges, 2–6 objects.
- Generalization to repeated colors, orthogonally touching objects, tied left edges, more than six objects, or arbitrary shape sizes is unmeasured.
- The random 100-lessons-per-band census does not exhaust all seeds or all possible external lesson assembly policies.
- No selected-task blocker remains. Audit-only peer findings are recorded in `WORK/AUDIT.md` and did not alter this generator.
## Current reviewer considerations

Source SHA-256: `5c1afcc5dcdc13ab461d1e327cf2ff8decb4300c0af524bf96f73f9ad2818756`.

# Decisions: 10bc62b2de84

## D1 / R1 — Keep the canonical authority and pin it

**Choice.** Keep the selected Racket rule unchanged and add `RULE_HASH = "eb9f505d4c6b"`.

**Rationale.** All four canonical labels agree with the independently written object-crop/left-sort/one-column-gap/bottom-pack oracle. The baseline defects were in input generation and contract enforcement, not in the authority.

**Alternatives considered.** Rewriting or simplifying the Racket program was rejected because there was no observed authority mismatch and any rule edit would add unnecessary compatibility risk.

**Probe/evidence.** Canonical task tests plus the public Racket-authority comparison; final `rule_smoke`, `racket_lint`, and `authority_sync` stages are green. Evidence: `checks/task-tests/result.json` and `checks/after/`.

**Failure mode / limitation.** A matching hash binds these bytes to the current canonical program; it does not prove that every conceivable lawful input is handled as a human might intend.

## D2 / R1 — Advertise only three exact, observable axes

**Choice.** Keep `grid_h`, `grid_w`, and `n_objects` as the only public controls. Validate call scalars and unknown keys before constructing `GenCtx`, and route both scheduled defaults and overrides through `draw_int_strict`.

**Rationale.** These axes are directly recoverable from pixels and useful to curriculum assembly. The old code sampled them outside keyed provenance and silently accepted misspellings/coercions, making a claimed exact control non-falsifiable.

**Alternatives considered.** Keeping ad hoc controls or declaring diagnostic-only axes was rejected because exact dimensions and object count can be honored constructively. Adding palette/shape/orientation knobs was deferred: they were not needed to fix the task and would enlarge the compatibility surface.

**Probe/evidence.** Override gate: 24,480/24,480 accepted draws across 272 cases and three bands, zero findings. Task tests cover both range corners and every 630 integer-axis combination.

**Failure mode / limitation.** The axes expose count and canvas dimensions only; shape-family and palette diversity remain internal.

## D3 / R2 — Replace capped retry/drop behavior with finite construction

**Choice.** Use shuffled candidate enumeration plus recursive backtracking. If the richer shape selection cannot fit, retry once with a compact shape family known to fit the advertised corner cases; otherwise raise an assertion instead of returning a partial scene.

**Rationale.** The red regression suite reproduced the old silent loss: a request for six objects returned five. A finite search makes success or failure explicit and keeps exact `n_objects` observable.

**Alternatives considered.** Raising the random retry cap was rejected because it remains probabilistic and can still lose requested objects. Shrinking the advertised domain was rejected because the full 6–14 × 9–22 × 2–6 domain is constructible.

**Probe/evidence.** `checks/task-tests-red.log` records the baseline failure. The final exhaustive test iterates all 630 combinations, and the strict override matrix adds 24,480 successful calls.

**Failure mode / limitation.** Backtracking cost grows with future shape-bank or count expansion. The current maximum of six compact objects is bounded and measured; widening it should add a performance/constructibility test first.

## D4 / R4 — Mix canonical anchors with a broad profile

**Choice.** Use a deterministic four-profile schedule: three canonical dimension/palette anchors (`7×9`, `7×10`, `9×10`, each with three objects/four colors including background) and one broader difficulty-scaled profile.

**Rationale.** The baseline had 0/60 exact canonical-profile hits and no band support. Anchors maintain direct support for the public distribution while the broad slot prevents the training set from collapsing to three canvas shapes.

**Alternatives considered.** Canonical-only generation was rejected as too narrow. A fully random profile was the baseline failure. Declaring a canonical-profile opt-out was rejected because support is inexpensive and appropriate.

**Probe/evidence.** Final profile floor: 45/60 exact and envelope hits, green in every band. Semantic profile coverage over 600 draws includes all four profiles in each band.

**Failure mode / limitation.** The profile sequence is deterministic for a given difficulty offset. The random lesson census samples consecutive requested starts but does not exhaust all seeds.

## D5 / R3 — Treat top alignment as the primary canonical shortcut

**Choice.** Declare `top_aligned` as the semantic rival and force unequal crop heights on every ordinary generated input.

**Rationale.** Every canonical object crop is height two, so top and bottom alignment produce identical public labels. This is a stronger and more task-specific shortcut than generic no-op or single-object rules.

**Alternatives considered.** Merely adding occasional unequal-height examples was rejected because a three-demo lesson could still contain only equal-height cases. Requiring unequal heights only in `strict_canonical_like` was also rejected because it would wrongly reject the canonical inputs.

**Probe/evidence.** Exact counterexample: `repo/generators/10bc62b2de84/counterexamples/top_aligned_shortcut.json`. The final semantic gate observes the witness on 600/600 draws, and the 300-lesson census refutes the rival in every production bundle and every query rotation.

**Failure mode / limitation.** This proves separation from one declared plausible rival, not all possible rules. Other undeclared distribution-specific shortcuts remain possible.

## D6 — Keep validation broader than the teaching guarantee

**Choice.** `self_check` and `strict_canonical_like` accept lawful equal-height canonical inputs; unequal heights are guaranteed by `generate`, not imposed as a universal law.

**Rationale.** Bottom alignment is semantically unobservable when heights match, but those examples are still lawful. Mixing validation with curriculum pressure would falsely reject canonical data and misstate the task domain.

**Alternatives considered.** A validator requiring unequal heights was rejected. A weak validator checking only dimensions/colors was also rejected because it would miss mixed-color components, duplicate left edges, invalid object sizes, and malformed grids.

**Probe/evidence.** Canonical 4/4 accepted, strict 600/600 generated draws accepted, malformed-grid tests return diagnostics instead of raising.

**Failure mode / limitation.** The validator describes the repaired sampler’s lawful manifold, not every grid on which the Racket program can execute.

## D7 — Use distinct colors, unique left edges, and no orthogonal touching

**Choice.** Give objects distinct colors, separate them under 4-connectivity, and make left bbox columns unique.

**Rationale.** These constraints make object identity and sort order unambiguous, so lessons teach crop/pack/alignment rather than accidental segmentation or tie-breaking behavior.

**Alternatives considered.** Same-color separated objects and tied left edges are valid research extensions but would add additional hypotheses and tie policies not needed for this repair.

**Probe/evidence.** `self_check`, `observe_overrides`, independent component extraction, and exhaustive axis tests.

**Failure mode / limitation.** This is a deliberate distribution restriction. Generalization to touching objects, repeated colors, or left-edge ties was not measured.

## D8 — Retain independent test tools and literal evidence

**Choice.** Add a task-local independent oracle, public Racket comparison, exhaustive domain test, and a small checked-in counterexample JSON.

**Rationale.** Future agents can distinguish generator mechanics from authority behavior and can replay the exact canonical shortcut without reconstructing it from prose.

**Alternatives considered.** Relying only on the shared battery was rejected because the battery does not exhaust the 630 joint integer-axis combinations or pin this task’s strongest rival input.

**Probe/evidence.** `repo/generators/10bc62b2de84/tests/test_generator.py` and `repo/generators/10bc62b2de84/counterexamples/top_aligned_shortcut.json`; 44/44 portable tests pass.

**Failure mode / limitation.** Exhaustion covers declared integer axes, not every seed, shape selection, or undeclared semantic rival.

## D9 — Do not claim an exhaustively checked schedule period

**Choice.** I briefly declared `LESSON_SCHEDULE_PERIOD = 4`, then removed the declaration after the semantic gate correctly reported `declared_period_not_enumerated`. The profile function remains deterministic, but the return makes no fixed-seed exhaustive-period claim.

**Rationale.** A metadata declaration should not imply evidence that was not actually run. The larger random census gives broad production/rotation evidence but is not the same as exhaustive schedule-period enumeration.

**Alternatives considered.** Running a separate fixed-seed period census was possible, but unnecessary once every ordinary input independently refuted the rival. Keeping the declaration with only a warning was rejected because the required final battery would remain non-green.

**Probe/evidence.** Intermediate warning: `checks/semantic-first/checks/10bc62b2de84_after_semantic_gate.log`. Final semantic evidence: `checks/semantic-second/` and `checks/after/`.

**Failure mode / limitation.** The 300-lesson census does not prove coverage for every seed or every conceivable assembly strategy.

## D10 / A1 / A2 — Keep peer audits read-only

**Choice.** Record reproducible peer findings and public-loader probes under `checks/audit/`, but do not edit either audited generator.

**Rationale.** The assignment explicitly asks for adversarial review, not repairs, and changing peer sources would contaminate source-bound conclusions.

**Alternatives considered.** No peer fixes were attempted.

**Probe/evidence.** `AUDIT.md`, `checks/audit/d19732b92d4a/`, and `checks/audit/2a08118e8823/`.

**Failure mode / limitation.** Findings remain open until their owners repair and reverify those exact source hashes.
