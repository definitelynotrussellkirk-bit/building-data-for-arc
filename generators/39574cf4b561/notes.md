# Working notes: 39574cf4b561

## 2026-09-28 review

The imported v2.0.1 generator omitted the singleton color-9 role present in every canonical input, rejected all five canonical inputs in `self_check`, exposed dead/degenerate axes, and had no task-linked semantic contract. The selected v3.0.0 implementation restored four linked canonical profiles, exact observable axes, strict unknown-key rejection, an independent rule mirror, and rival-verified semantic witnesses. The selected Racket rule was already correct and was not changed.

A task-local `workspace/role_signature_gate.py` was added because the generic morphology distribution gate was green on the defective baseline; per-color multiplicity signatures expose that blind spot directly.

## 2026-10-02 review

The v3.0.0 curriculum still made color 9 the singleton in every canonical and generated input. The wrong rule `never_complete_color_9` therefore matched all `5/5` canonical pairs and all `300/300` frozen-baseline samples (100 per band), despite being wrong whenever color 9 forms a three-corner rectangle. Evidence: `checks/baseline_color9_shortcut.json`.

Version 3.1.0 adds a scheduled role rotation. Samples with `sample_index % 3 == 2` make color 9 active and select a different singleton; the other two retain the canonical role. The analyzer, strict profile, palette observer, semantic witnesses, rival declarations, and lesson-identifiability hook were updated consistently. An initial every-other-sample schedule failed the generic strict-profile floor (`280/600`, 46.7%); the retained 2:1 schedule passes at `403/600` (67.2%) and guarantees both roles in every sliding three-demo window.

`workspace/lesson_shortcut_audit.py` now verifies declared canonical shortcuts against every canonical pair, audits all cyclic lesson starts over the deterministic 180-sample schedule period, and saves an exact disagreement. The final audit covers 180 lesson windows and 183 unique draws per band with zero invalid draws, zero role-incomplete windows, zero unidentifiable windows, and zero surviving `never_complete_color_9` lessons. Evidence: `checks/lesson_shortcut_audit_final.json`.

The selected Racket authority and canonical data were not changed. Remaining domain limits are deliberate: only canonical-linked canvas/profile tuples are emitted, rectangle row and column spans remain 2–4, and exactly one singleton is present.
## Current reviewer considerations

Source SHA-256: `f4c7fafb46c7ce7198424e22443545d82c7f304b730703e410915d02a7aca4e9`.

# Decisions: 39574cf4b561

## D1 — Keep the selected Racket rule and canonical data unchanged

- **Choice:** Repair only the generator curriculum and its task-local contracts.
- **Original rationale:** The earlier v3.0.0 notes stated that the selected Racket rule was already correct. No contrary evidence was found.
- **Alternatives considered:** Edit the Racket rule to special-case role rotation; change canonical examples; introduce a second authority.
- **Probe:** The rule-smoke stage executed the selected source on 120 final inputs, fired 120 times, matched the independent Python mirror 120/120, and passed reentrancy. Authority synchronization and execution parity also passed.
- **Failure modes avoided:** A generator-only teaching defect should not trigger an authority change; doing so would broaden review scope and risk canonical drift.
- **Limit:** The unchanged source still has two nonblocking Racket style advisories.

## D2 — Treat `never_complete_color_9` as the primary rival

- **Choice:** Model the strongest observed shortcut explicitly: complete all valid rectangles except color 9.
- **Original rationale:** Unknown as an explicit prior decision. The previous generator appears to have preserved canonical color roles for fidelity, but that made color identity perfectly predictive.
- **Alternatives considered:** Identity; complete only the first rectangle; fixed missing-corner orientation; erase the singleton. Those were already covered by existing witnesses and were less specific to the remaining defect.
- **Probe:** The rival matched all five canonical pairs and all 300 frozen-baseline samples, with zero active-9 examples. It disagrees on final easy seed 610000, sample index 2.
- **Failure modes:** A declared “shortcut” that does not actually fit every canonical pair would be invalid evidence. The audit therefore executes every declared canonical shortcut on all canonical pairs before lesson analysis.
- **Limit:** This does not prove it is the only human- or model-plausible rival; it is the strongest concrete one found and measured.

## D3 — Add exactly two lawful color-role assignments

- **Choice:** Support `canonical_9` and `rotated_9_active`.
- **Original rationale:** v3.0.0 required singleton 9 to match all canonical examples.
- **Alternatives considered:** Make any color independently active/singleton; remove the singleton; allow 9 to be absent; allow multiple singletons.
- **Reason:** The two-role design changes only the confounded feature while preserving count geometry, profile shapes, number of active rectangles, and one-singleton structure. It gives a clean intervention on color identity.
- **Probe:** `self_check` accepted all five canonical inputs and all final generated samples; 56/56 destructive mutations were rejected. The semantic witnesses for both roles fired.
- **Failure modes:** A rotated sample with neither active 9 nor singleton 9 would no longer test the shortcut. `_analyze` rejects it. A sample with active 9 and singleton 9 would violate distinct color/count roles and is also rejected.
- **Limit:** Color 9 is always present in one of the two roles; absence of 9 is outside this curriculum.

## D4 — Use a deterministic 2:1 role schedule

- **Choice:** Samples `0,1` modulo 3 are canonical-role; sample `2` modulo 3 is active-9.
- **Original rationale:** Unknown. The prior generator had no role schedule because it emitted only the canonical role.
- **Alternatives considered:**
  - **Random role draw:** rejected because frequency does not guarantee every lesson contains a counterexample.
  - **Strict alternation 1:1:** implemented first; rejected after the semantic gate measured only 280/600 strict samples (46.7%), below the declared 50% floor.
  - **Always active 9:** rejected because it would discard canonical color-role anchors.
  - **One active-9 example every four or more samples:** rejected because some three-demo windows would miss the decisive witness.
- **Reason:** Every length-three sliding window contains exactly one active-9 and two canonical examples, while the canonical share is exactly 2/3 over complete periods.
- **Probe:** All 540 final windows contained both roles; zero shortcut survivors; full-cycle strict fraction 122/183 per band. The generic semantic gate measured 403/600 (67.2%).
- **Failure modes:** Off-by-one lesson assembly or a changed `EXAMPLES_NEEDED` could invalidate the guarantee. The audit reads `EXAMPLES_NEEDED` and checks every cyclic start rather than assuming a single start.
- **Limit:** The guarantee is tied to sequential sample indices. A downstream sampler that picks three unrelated indices must run its own lesson-identifiability check.

## D5 — Lower `MIN_STRICT_FRAC` from 1.0 to 0.5, not below the repaired distribution

- **Choice:** Declare a 50% floor while producing approximately 67% strict canonical-role samples.
- **Original rationale:** v3.0.0 used 1.0 because every generated input was strict canonical-role.
- **Alternatives considered:** Keep 1.0, which would forbid any shortcut-breaking role; declare 2/3 exactly; reduce below 0.5 to make a 1:1 schedule pass.
- **Reason:** 0.5 expresses that canonical-role support must remain a majority-level component without coupling the gate to one exact schedule phase. The final generator exceeds it materially.
- **Probe:** The intermediate 1:1 schedule failed at 46.7%; the final schedule passed at 67.2%.
- **Failure modes:** Treating the threshold as a target could encourage unnecessary drift down to 50%. Reports therefore state both threshold and measured share.
- **Limit:** The generic gate samples hashed indices rather than an exact schedule period; the task-local audit supplies the exact 2/3 cycle result.

## D6 — Preserve existing public axes; keep role assignment internal

- **Choice:** Do not add `role_assignment` to `AXES`; derive it only from sample index.
- **Original rationale:** Existing axes were already exact and passed the override matrix.
- **Alternatives considered:** Expose a role override; overload `palette_kind`; make role random.
- **Reason:** Role rotation is a lesson-level teaching invariant, not a caller-controlled visual nuisance parameter. An unrestricted exact override could let a lesson request three canonical-only examples and reintroduce the shortcut. Keeping the schedule internal preserves the three-window guarantee and avoids expanding the 86-case override contract.
- **Probe:** Existing override stage passed 7,740/7,740 draws across all 86 cases and three bands after the change.
- **Failure modes:** A future requirement for targeted active-9 generation may justify an explicit override, but it must then declare lesson incompatibilities or enforce mixed-role assembly.
- **Limit:** External users cannot directly request a role through the public override API; they can select the corresponding sample-index phase.

## D7 — Recover palette kind from active colors excluding 9

- **Choice:** `observe_overrides` ignores active color 9 when classifying low/high/mixed palette kind.
- **Original rationale:** Palette kinds were defined over colors 1–8; 9 was previously reserved as singleton.
- **Alternatives considered:** Count 9 as a high color; redefine palette domains; stop observing palette kind on rotated samples.
- **Reason:** Including the mandatory active 9 would make every rotated low-palette sample appear high or mixed even though the sampled non-9 palette choice was low. Excluding 9 preserves the meaning and observability of the existing axis.
- **Probe:** The full override contract passed all cases; the semantic gate observed low, high, and mixed witnesses in every band.
- **Failure modes:** If a future palette definition explicitly includes 9 as a normal member, this observer and the axis documentation must change together.
- **Limit:** The role-specific presence of 9 is deliberately orthogonal to `palette_kind`.

## D8 — Keep singleton color distinct from all active colors

- **Choice:** In the rotated role, choose the singleton from unused colors 1–8.
- **Original rationale:** Canonical inputs use one distinct singleton color.
- **Alternatives considered:** Reuse an active color at a fourth location; choose 0; choose 9.
- **Reason:** Reusing an active color would change its count from three to four and destroy the clean “three corners versus singleton” signal. Color 0 is background; color 9 must remain active in this branch.
- **Probe:** Analyzer count constraints and task tests cover the role; final self-check found no violations.
- **Failure modes:** Palette exhaustion could leave no singleton choice, but at most four active colors are used from nine nonzero colors, so the candidate set is nonempty.
- **Limit:** Exactly one singleton remains a task-domain assumption.

## D9 — Add executable semantic declarations instead of prose-only claims

- **Choice:** Add `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, role witnesses, and `lesson_identifiable`.
- **Original rationale:** v3.0.0 already had executable witnesses for geometry and distractor behavior but not the color-9 confound.
- **Alternatives considered:** Mention the issue only in notes; add a single unit test; depend only on witness frequency.
- **Reason:** Frequency alone does not prove that a complete lesson refutes a rival. The lesson hook executes competitors on visible demonstrations and checks whether a surviving competitor changes the query.
- **Probe:** Generic semantic gate verified 15/15 witnesses, 15/15 rival claims, and 12/12 sampled lessons. The task-local audit tested all 540 cyclic windows.
- **Failure modes:** Copying rival names into an external tool can drift from source declarations. The tool imports and iterates the generator's actual mappings.
- **Limit:** Competitor coverage is finite and reviewer-authored, not universal induction.

## D10 — Audit the complete deterministic period

- **Choice:** Default task-local period 180 = `LCM(scene 4, missing 5, relation 4, palette 9, role 3)`.
- **Original rationale:** No prior full-cycle lesson audit existed.
- **Alternatives considered:** Only the minimum required 100 lessons per band; random sampling; one nonoverlapping partition of lessons.
- **Reason:** The schedule is small enough to exhaust all cyclic starts cheaply. Sliding windows catch phase-sensitive omissions that nonoverlapping groups miss.
- **Probe:** 183 draws are materialized per band to evaluate 180 starts with three demos plus one query. All inputs were unique in the final run.
- **Failure modes:** A new schedule factor could make 180 incomplete. The period basis is emitted in evidence and protected by a regression assertion, but future schedule changes still require updating the basis deliberately.
- **Limit:** The audit exhausts the deterministic schedule phases for the fixed seed family, not all possible RNG layouts or all conceivable rules.

## D11 — Preserve the failed schedule iteration

- **Choice:** Keep `checks/semantic_after/` and the earlier lesson-audit output rather than replacing them with only final green evidence.
- **Original rationale:** The return protocol requires failed iterations and counterexamples to remain visible.
- **Alternatives considered:** Delete the warning as obsolete; summarize it without raw evidence.
- **Reason:** It documents why 2:1 was chosen and proves the strict floor influenced the design rather than being retrofitted.
- **Limit:** The intermediate generator bytes are not packaged as a second source tree; the semantic report and source hash in that report retain the measured state.

## D12 — Solve from final bytes and declare prior exposure honestly

- **Choice:** Prepare the solve only after the final generator behavior was fixed; use challenge examples only during solving; declare earlier exposure `yes` and reference consultation `no`.
- **Original rationale:** Required by the assignment's solve policy.
- **Alternatives considered:** Claim a blind solve; consult the rule to validate masked answers; manufacture a wrong attempt for training contrast.
- **Reason:** The generator review necessarily exposed the family. The solve record should be useful without overstating independence.
- **Probe:** One solution revision passed 3/3 visible examples; `solve_episode.py finish` froze notes and provenance.
- **Freshness repair:** A later prose correction changed the generator bytes without changing behavior. The earlier solve was moved to `checks/prior-solve-generator-8e7ab42f/`, and a new solve was prepared and finished from the final `f4c7fafb…a7aca4e9` bytes rather than relabeling the old episode.
- **Failure modes:** Any generator-byte edit after solve preparation would invalidate freshness. The final generator hash still exactly matches `solve/summary.json`.
- **Limit:** Masked-query correctness is intentionally unknown.

## D13 — Treat the combined battery timeout as a verification limitation, not a code failure or a pass

- **Choice:** Report two incomplete combined invocations and retain complete individual stage runs.
- **Original rationale:** The duties request the combined command, while the return guide requires actual commands and honest blockers.
- **Alternatives considered:** Claim the individual stages imply the wrapper completed; mark all work blocked; omit the timeout.
- **Reason:** The individual stages directly verify every battery component against one final source hash, but they do not prove the orchestration command terminates in this environment.
- **Probe:** `checks/final_stage_summary.json` confirms all 12 final stage manifests bind to the same generator SHA and passed. `checks/after_battery_attempt.*` records the incomplete wrapper attempts.
- **Limit:** Maintainer replay of the exact combined command is still warranted.
