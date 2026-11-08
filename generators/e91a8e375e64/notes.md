# Current generator notes: e91a8e375e64

## Rule and authority

Five `P×P` panels are separated by all-5 columns: `A | B | C | D | Q`. Infer the unique dihedral transform from A→B and the cellwise recolor map from C→D, then apply transform followed by recolor to Q.

- Generator version: `3.0.0`
- Final reviewed generator SHA-256: `1823f963347c0f985a55c0422722c6b893d110e14c391615fa5e49e12590c355`
- Canonical rule pin: `RULE_HASH = "af51be6e4b66"`
- Racket authority changed in this review: **no**
- Prior return used as a lead: `review-41848cbb27980574:v0001`

## Current distribution

Public exact controls:

- `panel_size`: 3..5
- `n_map`: 2..4

Both are legal in every difficulty band and recoverable from the grid through `observe_overrides`. Unknown/obsolete keys and malformed scalar values fail loudly.

Useful style variation is internal, selected by `sample_index mod 4`:

1. `canonical`: 4×4, two-key map, six total colors, sparse public-like component grammar;
2. `varied`: difficulty-weighted size/map width and density;
3. `wide_map`: four map keys;
4. `big_panel`: 5×5, three map keys.

This reverses the earlier choice to advertise `density` and `texture`. Those names were not exact observable controls, several were inert, and negative textures produced self-check failures.

## Teaching assumptions

Generated examples require:

- one unique non-identity transform A→B;
- an injective non-identity C→D map;
- disjoint source and target palettes;
- every map source appears in A, C and Q;
- A and Q have eight distinct dihedral images.

Declared rivals are `recolor_only`, `transform_only`, and `unchanged_query`; corresponding witnesses and `lesson_identifiable` are executable. Production lessons use three demonstrations and one query. The period-four fixed-seed receipt checked all 12 band/start lessons and 48 query rotations; the wider census checked 300 lessons and 1,200 rotations with zero declared-rival ambiguity.

## Validation and tools

`self_check` validates shape, separators, unique transform, mapping support/consistency, non-identity/injectivity/disjoint palettes, source coverage and query asymmetry. `rule_mirror` is a Python diagnostic mirror.

`workspace/reference_probe.py` is an independent oracle and future-review tool. Focused tests live in `tests/test_generator.py`; portable result: 88/88 passed.

## Known limits

- Finite declared-rival checks are not a proof of unique induction.
- Fixed-seed schedule enumeration does not exhaust random support or rejected-pair schedules.
- The canonical component-count anchor is a coarse grammar match, not a full distribution metric.
- Disjoint source/target palettes deliberately restrict generated training examples to make recoloring visible; canonical lawful inputs remain accepted.
- Authority sync reports one archival raw-code copy as divergent, while the selected canonical authority and execution parity pass.

Primary final evidence:

- `checks/final/checks/e91a8e375e64_after_battery_summary.json`
- `checks/task-tests-portable-final/result.json`
- `checks/final_schedule/e91a8e375e64_schedule_period_s0.summary.json`
- `checks/lesson-census.summary.json`

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-68eac576afcc440f:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `1823f963347c0f985a55c0422722c6b893d110e14c391615fa5e49e12590c355`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported on unchanged source 1823f963347c0f985a55c0422722c6b893d110e14c391615fa5e49e12590c355. No issue within the bounded current-source scope. Eighty-eight tests pass; initial strict semantics lacks the required period receipt rather than failing a witness. A separate seed-0 enumeration covers all four starts across three bands: 12 lessons, 48 rotations and zero findings. The bound semantic rerun passes against recolor_only, transform_only and unchanged_query. The initial aggregate is not rewritten as green, and no universal rule-identifiability claim is made. Retain source-bound evidence: `checks/audit/e91a8e375e64/.combined.check.lock` `checks/audit/e91a8e375e64/.semantic-with-schedule.check.lock` `checks/audit/e91a8e375e64/combined/RUNTIME_MANIFEST.json` `checks/audit/e91a8e375e64/combined/checks/e91a8e375e64_audit_battery_summary.json` `checks/audit/e91a8e375e64/combined/checks/e91a8e375e64_audit_commands.jsonl` `checks/audit/e91a8e375e64/combined/checks/e91a8e375e64_audit_semantic_gate.json` `checks/audit/e91a8e375e64/combined/checks/e91a8e375e64_audit_semantic_gate.log` `checks/audit/e91a8e375e64/combined/checks/e91a8e375e64_audit_semantic_gate.receipt` `checks/audit/e91a8e375e64/combined/checks/e91a8e375e64_audit_summary.json` `checks/audit/e91a8e375e64/combined/checks/task_tests.xml` `checks/audit/e91a8e375e64/combined/progress.log` `checks/audit/e91a8e375e64/combined/result.json` `checks/audit/e91a8e375e64/schedule.json` `checks/audit/e91a8e375e64/schedule.summary.json` `checks/audit/e91a8e375e64/semantic-with-schedule/RUNTIME_MANIFEST.json` `checks/audit/e91a8e375e64/semantic-with-schedule/checks/e91a8e375e64_audit_battery_summary.json` `checks/audit/e91a8e375e64/semantic-with-schedule/checks/e91a8e375e64_audit_commands.jsonl` `checks/audit/e91a8e375e64/semantic-with-schedule/checks/e91a8e375e64_audit_semantic_gate.json` `checks/audit/e91a8e375e64/semantic-with-schedule/checks/e91a8e375e64_audit_semantic_gate.log` `checks/audit/e91a8e375e64/semantic-with-schedule/checks/e91a8e375e64_audit_semantic_gate.ok` `checks/audit/e91a8e375e64/semantic-with-schedule/checks/e91a8e375e64_audit_semantic_gate.receipt` `checks/audit/e91a8e375e64/semantic-with-schedule/checks/schedule-census-input.json` `checks/audit/e91a8e375e64/semantic-with-schedule/progress.log` `checks/audit/e91a8e375e64/semantic-with-schedule/result.json`

### Assessment or prior finding

## e91a8e375e64

**No generator issue found in the bounded current-source audit.** I inspected the five-panel transform-plus-recolor contract, exact `panel_size`/`n_map` controls, executable rivals, and the current task tests. The official portable audit run executed **88/88 tests successfully**. Its first semantic invocation reported only that the declared four-step schedule had not yet been enumerated, not a failed witness or ambiguous lesson.

I then enumerated every declared start at seed 0 across easy, medium, and hard: **12/12 lessons** and **48/48 query rotations** materialized, with zero ambiguities, hook warnings, or scoring errors. The strict semantic gate passed when bound to that source-hashed receipt. This is finite coverage of the declared rivals (`recolor_only`, `transform_only`, `unchanged_query`), not proof against every possible shortcut.

Current generator SHA-256: `1823f963347c0f985a55c0422722c6b893d110e14c391615fa5e49e12590c355`; canonical rule source SHA-256: `af51be6e4b66ccda203a50eee145bb3503838335a59ad9a34a683c8912f9f3b4`.

Evidence:

- `checks/audit/e91a8e375e64/combined/result.json` — portable tests pass; initial semantic warning records the missing schedule receipt.
- `checks/audit/e91a8e375e64/schedule.json` and `.summary.json` — complete fixed-seed period enumeration.
- `checks/audit/e91a8e375e64/semantic-with-schedule/result.json` — strict semantic pass with required rotations.

No audited source was edited.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `1823f963347c0f985a55c0422722c6b893d110e14c391615fa5e49e12590c355`.

# Decisions: e91a8e375e64

## D1 — Keep the authoritative rule unchanged and pin it

**Prior choice:** the generator had no `RULE_HASH`, so a correct-looking Python distribution was not explicitly bound to the selected Racket authority.

**Decision:** keep the canonical rule unchanged and add `RULE_HASH = "af51be6e4b66"`.

**Reason:** canonical pairs and the independent Python oracle already agreed with the intended five-panel transform-plus-recolor rule. The defects were in sampling, controls and teaching support, not in the rule.

**Rejected alternative:** edit/simplify the Racket program. That would widen the review surface without addressing the measured generator failures.

**Probe:** final rule-smoke, Racket lint and authority-sync stages are green; execution parity is `PASS`. The authority check still reports an archival raw-code copy as divergent, but the selected canonical authority is exactly synchronized.

**Failure mode/limit:** any future canonical rule change invalidates this pin and requires re-verification.

## D2 — Expose only exact grid-observable controls

**Prior choice:** `panel_size`, `n_map`, `density` and `texture` were public. Difficulty-local default ranges rejected values declared globally valid; texture modes included negative fixtures; several texture/density combinations were inert; unknown keys were swallowed.

**Decision:** expose only `panel_size=3..5` and `n_map=2..4`. Validate seed, sample index, difficulty and unknown keys strictly. Record exact requested values through fixed `GenCtx.draw_int` calls and recover them with `observe_overrides`.

**Reason:** public controls should be falsifiable from output bytes. Panel size and mapping width are exact. A label such as `density="med"` or `texture="varied"` is not exact when multiple random grids can represent it and the old code silently ignored it in some branches.

**Rejected alternatives:**

- Preserve old labels and add many incompatibility declarations: still leaves a non-observable semantic contract.
- Make difficulty shrink the legal domain: conflicts with a single advertised `AXES` domain and caused the original endpoint failures.
- Keep negative fixtures in ordinary texture values: makes `generate` produce examples rejected by `self_check`.

**Probes:** all 27 `(band, panel_size, n_map)` combinations round-trip in focused tests; shared override stage reports `PASS`, no findings/warnings, and rejects the unknown-key probe.

**Failure mode/limit:** callers depending on obsolete `density`/`texture` keys now receive an explicit error. This is intentional fail-loud behavior.

## D3 — Move useful variation into a period-four internal schedule

**Prior choice:** named textures attempted to control variation, but `varied`, `wide_map` and `big_panel` were byte-identical to untextured draws for sampled seeds.

**Decision:** use four internal profiles selected by `sample_index mod 4`: `canonical`, `varied`, `wide_map`, `big_panel`. Declare `LESSON_SCHEDULE_PERIOD = 4`.

**Reason:** a deterministic schedule guarantees recurring coverage without pretending that an internal style label is an exact public axis. It also makes complete cyclic-start enumeration cheap.

**Rejected alternatives:** independent random profile choice can produce long local gaps and cannot be exhaustively checked by start residue; always canonical would collapse diversity.

**Probes:** focused tests cover 80 defaults per band and every four-example window; fixed-seed schedule census covers all four starts in all three bands.

**Failure mode/limit:** the declared-period receipt exhausts starts only at seed 0. Random layout support remains sampled rather than proven.

## D4 — Add a structural canonical anchor, not just a size/palette match

**Prior choice:** zero of 60 baseline draws matched canonical profile `(4, 24, 6)`.

**Decision:** the canonical schedule slot uses 4×4 panels, a two-key mapping, exactly six total colors, and sparse panel templates that match the public examples' connected-component count range.

**Reason:** profile-floor matching by dimensions and palette alone can still miss the public grammar. The additional component witness keeps generated examples on the same sparse structural manifold while remaining non-identical and asymmetric.

**Rejected alternatives:**

- Rely only on random chance for a 4×4/two-map draw: baseline demonstrated 0/60 support.
- Copy a canonical grid: destroys diversity and risks memorization.
- Force every example to be canonical-like: undercovers larger panels and wider mappings.

**Probes:** the regression test compares generated canonical-slot component counts against all public inputs; final profile-floor and defect-lint stages are green.

**Failure mode/limit:** connected-component overlap is a coarse grammar statistic, not a complete distribution-distance guarantee.

## D5 — Make transformation and recoloring necessary in each example

**Prior choice:** random symmetries, absent map keys or identity-like mappings could make one operation observationally unnecessary even when the saved label was correct. No executable semantic contract existed.

**Decision:** require unique non-identity A→B geometry; injective non-identity C→D recoloring with disjoint palettes; complete source-color coverage in A/C/Q; and eight distinct dihedral images for A and Q. Declare the rivals `recolor_only`, `transform_only`, and `unchanged_query` plus corresponding witnesses.

**Reason:** Qwen training value depends on demonstrations teaching the composition, not merely producing valid labels. Each example now contains a direct counterexample to omitting either operation.

**Rejected alternatives:** resample only at lesson level. Per-example necessity is cheaper, makes every query position safe, and avoids brittle dependence on one special demonstration.

**Probes:** focused tests check 96 examples and every query rotation of 36 four-example windows. The wider census checks 300 production lessons and 1,200 rotations with zero declared-rival ambiguity.

**Failure mode/limit:** the rival set is deliberately finite. It does not establish unique induction against every possible program.

## D6 — Use disjoint source/target palettes and complete key coverage

**Prior choice:** colors could map to themselves or overlap roles, allowing a recolor operation to be partially invisible.

**Decision:** sample `2*n_map` distinct non-background/non-separator colors, using the first half as source keys and the second half as targets. Ensure A, C and Q contain exactly all source keys.

**Reason:** every mapping key changes visibly and is demonstrated before appearing in Q. With at most four keys and eight available colors, the constraint is always satisfiable.

**Rejected alternative:** permit palette overlap but require at least one changed key. That still teaches partial-copy shortcuts and complicates exact semantic witnesses.

**Probe:** validator mutations cover identity mappings, support mismatch and unknown query colors; all focused tests pass.

**Failure mode/limit:** this is a stricter training distribution than the entire mathematical rule domain. It is intentional because the generator is for teachable examples, while canonical inputs remain accepted.

## D7 — Add an independent oracle and portable tests

**Prior choice:** the assigned task had no focused tests for the measured failures.

**Decision:** add `tests/test_generator.py` and `workspace/reference_probe.py`. The probe independently splits panels, enumerates dihedral transforms, infers the map, calculates rivals and observes controls.

**Reason:** testing `rule_mirror` only against helpers from the same module would preserve correlated bugs. The independent probe also gives future agents a reusable inspection tool.

**Rejected alternative:** rely only on the shared battery. The battery found the broad contract defects but does not encode all task-local structural and window-rotation invariants.

**Probe:** the test suite was observed failing before implementation (70 failures) and now passes 88/88 in the portable task-test runtime.

**Failure mode/limit:** the oracle and production implementation are both Python; Racket rule-smoke and authority execution parity remain necessary independent checks.
