# Working notes: ae7376fe4957

## Final repair, 2026-10-07

- **Teaching defect:** the original four-pair schedule could place its only multi-red counterexample in the held-out query.  For `(difficulty="easy", seed=0, start=3, query_index=2)`, the remaining three demonstrations did not distinguish the intended first-red rule from `drop_all_red_payload`, `use_last_red_target`, or `use_nearest_red_target`.
- **Distribution repair:** canonical anchors remain every fourth default draw, while every non-anchor default draw now contains one or two later red payload cells.  Consequently every three-demo rotation of a four-pair lesson contains a multi-red witness. Exact `extra_reds=0` overrides and zero-red canonical anchors remain supported.
- **Rival-totality repair:** a generated scene now retains at least one surviving non-red payload cell. This prevents `drop_all_red_payload` from predicting an empty, invalid ARC grid during semantic scoring.
- **Contract cleanup:** presence-only coverage probes (canonical profile, no-clipping, and four shift quadrants) were removed from `SEMANTIC_WITNESSES`; task tests continue to measure them directly. Every remaining semantic witness has an executable rival claim.
- **Portable regression:** task tests use `reviewer_support.find_root` and `canonical_pairs`, check all 9,216 deterministic query rotations (3 bands × 16 seeds × 48 starts × 4 query positions), and exercise the declaration-driven workspace shortcut auditor.
- **Reusable probe:** `workspace/shortcut_audit.py` reads the generator's current shortcut declarations, verifies them against all canonical pairs, finds generated refutations, and checks every query position in deterministic lesson windows.

## Limitations

The finite competitor set does not prove unique induction against every imaginable rule. The sampler intentionally concentrates non-anchor defaults on multi-red cases to guarantee first-target identifiability; canonical anchors and exact overrides preserve no-extra-red coverage. The Racket authority and canonical outputs were not changed.
## Current reviewer considerations

Source SHA-256: `f77778526971901edf0623c1446ed4196ac9e61543ca08839d363cb6c0e09b17`.

# Decisions: ae7376fe4957

## D1 — preserve the Racket authority and canonical rule

**Choice.** Keep the canonical Racket row and `RULE_HASH="072dc737db06"` unchanged.

**Rationale.** The rule itself is coherent and all four canonical pairs are exactly reproduced by the independent Python mirror: find the unique blue(1) source, choose the row-major first red(2) target, translate every other nonzero cell—including later red cells—clip at the canvas, and tightly crop the survivors. The reproduced defect was in lesson sampling, not labelling or authority.

**Rejected alternatives.** Changing the rule to nearest-red would fit the four canonical demonstrations but contradict the task's selected authority and generated first-vs-nearest witnesses. Changing canonical outputs would therefore hide the shortcut rather than repair the teaching distribution.

**Probe/failure mode.** `checks/shortcut-answer/racket.json` independently verifies a case where first-red and nearest-red differ. The final battery's rule-smoke, racket-lint, and authority-sync stages are green.

## D2 — make every non-anchor default draw multi-red

**Choice.** Replace the general default `sample_index % 3` schedule with `1 + sample_index % 2`; retain the existing canonical anchor every fourth no-override draw.

**Rationale.** A production lesson has three demonstrations and one query. A four-pair window contains at most one anchor, so any held-out position leaves at least two general draws with later-red payload. Those examples distinguish the row-major-first target from nearest/last target selection and distinguish copying later reds from dropping them.

**Rejected alternative: only fix the observed residue.** Patching sample 5 or one schedule residue would leave other held-out positions or shifted windows vulnerable.

**Rejected alternative: force four demonstrations.** `EXAMPLES_NEEDED=3` is part of the selected task interface; increasing it would alter downstream lesson shape and still avoid addressing weak individual examples.

**Rejected alternative: remove anchors.** Anchors provide exact canonical-size/palette coverage and preserve ordinary single-red cases. Keeping them also prevents the default distribution from collapsing to only one morphology.

**Probe/failure mode.** `checks/rotation-ambiguity-before.json` is the baseline counterexample. The task test checks 9,216 rotations, and `workspace/shortcut_audit.py` can be rerun whenever rivals or scheduling change.

## D3 — preserve at least one surviving non-red payload cell

**Choice.** During scene construction, require one selected translated survivor that is neither a marker nor a later red payload cell.

**Rationale.** The declared `drop_all_red_payload` rival should produce a valid nonempty alternative output so the semantic scorer can compare it with the intended answer. Before this change, a lawful generated scene could translate only red survivors; the rival then returned `[]` and the shared grid validator raised instead of registering a refutation.

**Rejected alternative: special-case the rival to return a placeholder.** That would change the rival's meaning and could create artificial disagreements unrelated to the intended concept.

**Rejected alternative: ignore rival exceptions.** Suppressing the exception would turn incomplete semantic evidence into a false clean result.

**Probe/failure mode.** The minimal failing draw is `difficulty="easy", seed=0, sample_index=7`; `checks/drop-red-rival-red.log` records red, and the final regression plus 300-lesson census record green.

## D4 — reserve `SEMANTIC_WITNESSES` for rival-bearing claims

**Choice.** Remove canonical-profile, no-clipping, and four shift-quadrant presence probes from `SEMANTIC_WITNESSES`; continue testing those properties directly in `test_default_schedule_covers_profiles_branches_and_rivals_in_each_band`.

**Rationale.** The shared contract interprets semantic witnesses as evidence against named rivals. Presence coverage and rival refutation are both useful but are different claims. Keeping them separate eliminates blocking weak-witness diagnostics without deleting the coverage measurement.

**Rejected alternative: invent rival mappings.** Assigning arbitrary rivals to shift-quadrant or canonical-profile presence would make the contract syntactically green while weakening its semantic meaning.

**Limitation.** A shared `COVERAGE_WITNESSES` declaration would express this distinction better; that is the top tooling proposal in `FEEDBACK_TO_CODEX.md`.

## D5 — use only public portable test helpers

**Choice.** Replace the private `scripts.canonical_profile_gate` import with `reviewer_support.find_root` and `canonical_pairs`; resolve workspace files from the discovered root and task ID.

**Rationale.** The selected task tests are intentionally copied into two staged layouts. Fixed parent-depth paths and reviewer-private modules are not part of the portable task API.

**Rejected alternative: skip the frozen duplicate.** The duplicate is what caught the first nonportable workspace path. Both copies should execute to prove the test package is relocatable.

**Probe/failure mode.** `checks/task-tests-final/result.json` records the fixed-depth failure; `checks/task-tests-final2/result.json` records 26/26 passed with the public-root approach.

## D6 — add a declaration-driven shortcut audit rather than another one-off script

**Choice.** Build `workspace/shortcut_audit.py` around the current `CANONICAL_SHORTCUTS` declaration.

**Rationale.** Future agents can add or rename competitors without updating a parallel hard-coded list. The tool reports canonical-fitting shortcuts, finds generated refutations, and rotates each query position across deterministic windows.

**Rejected alternative: inspect only the canonical pairs.** Canonical fit finds the dangerous shortcut but cannot show whether the generator actually emits disambiguating cases.

**Limitation.** The tool only certifies declared rivals and its configured finite seed/start range. It complements, rather than replaces, the source-bound census and shared semantic gate.

## D7 — retain both production-order and rotation evidence

**Choice.** Require arbitrary query rotations for this generator and report production and rotation counts separately.

**Rationale.** The downstream assembly can hold out any one pair, and the reproduced defect appeared only after rotating the query. An ordered-only pass would therefore be insufficient.

**Evidence.** Final production census: 300 lessons / 1,200 pairs, zero ambiguity or scoring error. Final rotation census: 1,200 rotations, zero ambiguity or scoring error. Shared smoke test: 48/48 rotations. Deterministic task regression: 9,216/9,216 rotations.
