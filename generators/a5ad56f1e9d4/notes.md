# Working notes: a5ad56f1e9d4

## 2026-10-06 review `review-3b0e88875e3c4167`

- Baseline generator SHA: `7cc5ea9034a1016a2616a899e82a8fd34c5f9915deeea57e4d66b92115f1f9cb`.
- Final generator SHA: `9ae0ed6f8da92019c50f0260a4d18c27935feb92a1d33cef02f2f9696c8c7049`.
- Selected rule hash remains `7cf87a6a8bce`; no Racket/canonical bytes changed.
- Baseline defects: rejected all canonical inputs through a mandatory gap, excluded canonical 3×4 geometry, had dead/misleading axes, and used shortcut-prone above/right marker placement.
- Repair: exact 2..4 rectangle dimensions, contact/tie/order controls, exhaustive constructive layouts, four-side scheduling, canonical anchors, and dual witnesses against Euclidean distance and reading-order ties.
- Completed after battery: 12/12 green.
- Portable task tests: 11/11 passed.
- Source-bound lesson census: 300/300 materialized, 0 production ambiguity, 0/1,200 rotated-query ambiguity, 1,195 unique inputs.
- Reusable fast probe: `workspace/probe_curriculum.py`; it is Python-mirror diagnostic evidence and does not replace Racket checks.

## Future checks

Rerun the task-local probe, full battery with `--require-rotations-identifiable`, portable task tests, and 100-lessons-per-band source-bound census after changing any axis, schedule cadence, rival, `EXAMPLES_NEEDED`, or rule bytes. Any new canonical profile outside the current 2..4 domain requires an explicit grammar review.
## Current reviewer considerations

Source SHA-256: `9ae0ed6f8da92019c50f0260a4d18c27935feb92a1d33cef02f2f9696c8c7049`.

# Decisions for `a5ad56f1e9d4`

## D1 — Treat the selected rule as authoritative

**Choice.** Keep the selected Racket rule and canonical rows unchanged; repair only the generator, tests, and task documentation.

**Rationale.** Rule-smoke already showed the selected authority solved the three canonical pairs. The observed failures were generator-domain and curriculum failures, not rule-execution failures. After repair, the selected authority set hash remained `95b9baf70f62dc23ee99725e98fb12e6d8ac2466f99246d4b135e8381c6a7005`, and authority synchronization passed (`checks/after-final/checks/a5ad56f1e9d4_after_authority_sync.json`).

**Rejected alternative.** Rewriting the archival or selected Racket source would create unnecessary authority drift and exceed the evidence. The archival selected-source distinction is preserved rather than normalized away.

**Future check.** Any later rule-byte change must update `RULE_HASH`, replay all canonical pairs, and rerun authority synchronization before generator evidence is reused.

## D2 — Own the canonical 2..4×2..4 rectangle domain

**Choice.** Accept exactly one solid color-5 rectangle with height and width 2..4, plus exactly two distinct singleton markers outside it.

**Rationale.** The three canonical profiles include 3×3, 2×3, and 3×4 rectangles. The baseline 2..3 cap excluded 3×4, while its mandatory gap rejected every canonical input. The new bounds are the smallest simple domain that contains the selected canonical evidence.

**Rejected alternatives.** Retaining the 2..3 cap would continue to disown canonical data. Expanding to arbitrary 1..30 rectangles would be unsupported by the selected examples, inflate the constructive layout search, and add untested degenerate shapes.

**Failure modes.** A future canonical profile outside 2..4 would make the generator stale. Hollow, disconnected, or multi-rectangle color-5 shapes remain invalid because the selected rule is taught as one solid target rectangle.

**Probe.** Canonical ownership and mirror equality are checked in `test_canonical_inputs_are_owned_and_python_mirror_matches_authority` and summarized in `checks/a5ad56f1e9d4-workspace-probe.json` as 3/3.

## D3 — Allow both contact and separation

**Choice.** Make `contact_mode` an exact axis with `touching` and `gapped` values.

**Rationale.** Canonical examples contain touching geometry, so forbidding contact was wrong. Gapped examples prevent learners from equating the rule with edge-adjacent flood fill and broaden distance evidence.

**Construction.** `touching` means at least one marker is Manhattan distance 1 from the rectangle. `gapped` means both are distance at least 2. Each marker must still be strictly nearest to at least one rectangle cell.

**Rejected alternative.** A probabilistic “usually touching” flag would not be externally observable or exactly overrideable.

**Probe.** All 72 joint axis products round-trip through `observe_overrides`; shared override evidence is in `checks/after-final/checks/a5ad56f1e9d4_after_override_results.json`.

## D4 — Expose tie presence and marker order explicitly

**Choice.** Add exact `tie_mode` (`avoid|include`) and `marker_order` (`lower_first|lower_second`) axes.

**Rationale.** The canonical pairs do not uniquely distinguish Manhattan tie-breaking by lower color from tie-breaking by marker reading order. Both the existence of a tie and the relative position of the lower color must be pixel-observable for a lesson to teach the intended rule.

**Rejected alternatives.** An axis named only for palette or random marker colors would not certify that a tie occurs. Always placing the lower color first makes the reading-order rival indistinguishable.

**Failure modes.** Merely including ties is insufficient if lower color and reading order agree. The production non-anchor schedule therefore fixes `tie_mode=include` and `marker_order=lower_second` while exact overrides still cover every combination.

**Probe.** `SEMANTIC_WITNESSES`, `WITNESS_RIVALS`, the task tests, and the 300-lesson Racket census jointly check these choices.

## D5 — Use constructive layout enumeration, not capped rejection

**Choice.** Enumerate legal rectangle origins and marker pairs, filter them by requested controls and witness constraints, then choose deterministically from the resulting pool.

**Rationale.** Exact controls should fail only when the declared product is mathematically impossible. Random rejection with a retry cap can fail a legal but rare combination and makes the override contract seed-dependent.

**Rejected alternative.** Increasing a retry cap would hide rather than remove the failure mode.

**Failure modes.** The finite pool can become expensive if future domains grow substantially. The current 2..4 domain is cached and completed within the gate budget; broader domains should use a more structured constructive solver.

**Probe.** `workspace/probe_curriculum.py` exhausts all 72 declared products. Unknown keys are separately tested to fail loudly.

## D6 — Cycle all marker sides

**Choice.** Schedule target-side coverage across top, right, bottom, and left, while allowing corner placements to count for two sides.

**Rationale.** The baseline's persistent above/right relation offered a positional shortcut unrelated to nearest distance. Four-side coverage removes that fixed relation and gives the same rule under reflected arrangements.

**Rejected alternative.** Unconstrained random sides might look diverse in a sample while still omitting a side in a small lesson stream.

**Probe.** `test_default_distribution_varies_marker_sides_contact_and_rectangle_geometry` requires the complete side set, both contact modes, and the canonical shape subset.

## D7 — Use a period-three lesson schedule

**Choice.** Every third sample is a canonical-profile anchor; the other two samples are dual rival witnesses. Production lessons use three consecutive demonstrations and one query.

**Rationale.** The shared profile-floor requires canonical support in each band, while every demonstration set must refute both canonical-fitting shortcuts. In any four consecutive materialized pairs, removing any one as query leaves at least one non-anchor dual witness among the three demonstrations.

**Rejected alternatives.** All anchors would overfit canonical morphology and may not refute either rival. All adversarial examples would miss canonical-profile support. A four- or six-phase schedule without proof could produce query rotations that remove the only witness.

**Ordering/query policy.** Consecutive starts are intended. Arbitrary held-out query positions are supported and were required in the semantic gate. The source-bound census found 0/1,200 ambiguous rotations; the task-local exhaustive-start probe found 0/180.

**Failure modes.** The result is finite-rival identifiability, not universal induction. Adding a rival, changing `EXAMPLES_NEEDED`, or altering cadence invalidates the argument.

**Probe.** Run `workspace/probe_curriculum.py` after any schedule change, then rerun the Racket-labelled `lesson-census --per-band 100 --rotate-query`.

## D8 — Keep anchors deterministic but layouts seed-sensitive

**Choice.** Schedule semantic roles from `sample_index`, while selecting among many valid layouts and colors from the keyed generator context.

**Rationale.** Deterministic role scheduling proves coverage in short streams. Seed-sensitive layout choice supplies variation without risking missing required witnesses.

**Rejected alternative.** Pure seed-driven semantic roles make coverage probabilistic. Fully fixed grids would duplicate data and encourage memorization.

**Observed result.** The 300-lesson census contained 1,195 unique inputs among 1,200 pairs, while retaining exact schedule guarantees (`checks/lesson-census-final.json`).

## D9 — Preserve colors 0 and 5 as fixed roles

**Choice.** Keep 0 as background, 5 as the target rectangle, and choose two distinct marker colors from `{1,2,3,4,6,7,8,9}`.

**Rationale.** These roles are fixed by the selected task. Arbitrary permutation of 0 or 5 would change the task rather than augment it. Marker colors can vary, but lower numeric color remains semantically relevant on ties.

**Rejected alternative.** Treating marker colors as fully interchangeable would erase the tie rule. Numeric-rank variation is retained specifically so lower-color evidence appears under many palettes.

## D10 — Retain a Python mirror only as a test contract

**Choice.** Implement `rule_mirror` and two rival oracles in the generator module for self-checking, witnesses, and lesson scoring, but continue to use the selected Racket rule for source-bound labels and acceptance evidence.

**Rationale.** The mirror enables fast exhaustive task-local tests; Racket execution prevents circular acceptance.

**Limitation.** A mirror bug could make the workspace probe falsely green. That is why the completed battery, canonical rule-smoke, and 300-lesson Racket census are reported separately.

## D11 — Exact override contract

**Choice.** Reject unknown axes and wrong types, construct every declared joint product, and recover requested values from output pixels.

**Rationale.** Silent ignore, metadata-only controls, and undeclared incompatibilities make generated training distributions unreviewable. The baseline displayed these failure modes.

**Rejected alternative.** Declaring broad incompatibility tables was unnecessary because all 72 combinations are constructible.

**Probe.** Shared override gate: 6,300 generated draws, zero findings. Task tests: all 72 products plus four unknown-key cases.

## D12 — Stop at the canonical-supported grammar

**Choice.** Do not add more markers, multiple rectangles, non-solid rectangles, alternative target colors, or shape-changing outputs.

**Rationale.** Those are new task hypotheses, not repairs supported by the selected authority. The current change fixes ownership and teaching sufficiency without broadening semantics.

**Known limitation.** Models trained only on this generator are not shown extrapolation to more than two markers or rectangles larger than 4×4. Such extensions require new authority-backed examples or an explicit reviewed generalization decision.

## Current scoped audit assessment

See `evidence/current-audit-assessment.json` for explicit source-bound dispositions. These are finite reviewer-reported checks; no owner rerun or universal qualification.
