# Working notes: d3c9fc4479d8

## Review 2026-10-04 — generator 2.0.0

The 1.1.1 baseline had a correct transformation but a weak data contract: no pinned `RULE_HASH`, ignored/singleton controls, permissive validation, no canonical-profile support, and no executable lesson-identifiability contract. The repair leaves the Racket authority unchanged and replaces only the selected generator/test/notes/workspace surface.

Key decisions and limits are in packet-root `DECISIONS.md`; maintainer results and hashes are in `REVIEW.md`. Reusable curriculum verification is `workspace/lesson_probe.py`. Final authoritative evidence:

- `checks/after/checks/d3c9fc4479d8_after_battery_summary.json` — 12/12 stages green.
- `checks/task-tests-official/result.json` — 27/27 task tests.
- `checks/lesson-census.json` — 300 lessons / 1,200 rotations, zero declared-rival ambiguity.
- `checks/lesson-probe.json` — all cyclic starts and legal query rotations for the four-slot schedule.

The validator intentionally accepts canonical width 6 and 8-connected diagonal source components, while generated exact controls use width 7–14 and compact 2×2-local components. Generated lessons have two or three compact pairs and at most one unmapped control. These are training-manifold restrictions, not additional Racket-rule requirements.

Finite named-rival checks do not prove universal identifiability. Imported associated notes remain in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `6c62829b8afe5a427ff913d5a8e4b905c78cb524110800bb740c2bff1353801c`.

# Decisions for `d3c9fc4479d8`

This file records selected-task design choices, the evidence that drove them, rejected alternatives, and limits. The original 1.1.1 rationale was not present beyond its brief summary, so “original rationale” below is explicitly unknown unless the source made the intent observable.

## D1 / R1 — Replace the advertised axis surface rather than preserve names

**Choice.** Expose seven exact controls: `grid_h`, `grid_w`, `n_pairs`, `source_uses`, `legend_offset`, `mapping_overlap`, and `control_kind`.

**Original rationale.** Unknown. The baseline exposed controls such as position/density that did not change output observably, and some accepted values produced identical bytes.

**Alternatives considered.** Keep the old names and reinterpret them; retain singleton axes for compatibility; or delete all overrides and rely on schedule-only variation. Reinterpretation would hide a breaking semantic change behind familiar names, singleton controls would continue to mislead the override auditor, and no overrides would remove useful exact regression handles.

**Probe.** The before override report contained 5,731 findings. The final exhaustive test generates every exact Cartesian combination in each difficulty setting, and the final override stage expands to 29,070 successful draws with no findings.

**Failure modes and limits.** Existing external callers using undocumented old keys now receive an explicit `ValueError`. This is deliberate: accepting an axis that does not control pixels is worse for data provenance than an honest incompatibility.

## D2 / R1–R3 — Generate two or three legend pairs, not one to three

**Choice.** `n_pairs` is exactly 2 or 3.

**Original rationale.** The baseline accepted one-pair cases, but no retained rationale explained why.

**Alternatives considered.** Preserve one-pair support; require exactly two; allow up to four. One pair cannot teach pair scanning versus single-color replacement and weakens reverse/fixed-origin counterexamples. Exactly two would omit a canonical three-pair profile. Four pairs would exhaust the ten-color palette under disjoint mappings and controls and is not required by the canonical examples.

**Probe.** All four canonical pairs pass the validator; the schedule includes both counts; 60/60 strict draws and all exact override combinations pass.

**Failure modes and limits.** The generator no longer samples lawful one-pair instances. The canonical rule could apply to them, but they are excluded from the training manifold because they provide less evidence about legend parsing.

## D3 / R4 — Use a four-slot curriculum with three demonstrations

**Choice.** Cycle four profiles: canonical two-pair with control; shifted two-pair chain; canonical three-pair with control; shifted three-pair chain. Assemble lessons with three demonstrations and one query.

**Original rationale.** Unknown; the baseline had no executable lesson contract.

**Alternatives considered.** Independent random draws; a three-slot cycle; four demonstrations; or resampling only after an ambiguity is found. Independent draws can omit a needed witness. A three-slot cycle cannot make all three-demo/query rotations simultaneously include both shifted/chain evidence and a preserved control without collapsing useful variety. Four demonstrations would solve the coverage problem at higher token cost. Reactive resampling makes provenance and reproducibility harder.

**Probe.** `workspace/lesson_probe.py` checks all 4 cyclic starts × 3 bands × 4 held-out query positions. The independent production census checks 300 lessons and 1,200 rotations. Both report zero declared-rival ambiguities.

**Failure modes and limits.** This guarantee applies to the declared four-slot assembly and one-query rotations. A downstream assembler that changes the number of demonstrations or splices unrelated samples must rerun the semantic gate.

## D4 / R3 — Pin two canonical coarse anchors per band

**Choice.** Slots 0 and 2 use `(height,width,palette)=(4,7,5)` and `(4,8,7)`; broad slots vary by difficulty.

**Original rationale.** The baseline sought broad random sizes but had no explicit canonical-profile reservation.

**Alternatives considered.** Fully random dimensions; duplicate all four exact canonical input shapes; or one anchor only. Fully random produced 0/60 profile hits. Duplicating all canonical shapes would reduce diversity and overfit layouts. One anchor risks missing three-pair/palette support.

**Probe.** Before profile floor was advisory at 0/60. Final profile floor has 36/60 exact/envelope hits with support in every 20-draw band, while diversity remains 300/300 unique inputs and outputs.

**Failure modes and limits.** Coarse-profile equality does not recreate canonical cell layouts. It preserves shape/palette neighborhoods, not memorized examples.

## D5 / R4 — Include shifted legends

**Choice.** Half the scheduled profiles place the compact legend at column 1 instead of column 0.

**Original rationale.** The baseline scanner intended to find adjacent pairs, but generated evidence did not reliably challenge an origin-fixed shortcut.

**Alternatives considered.** Always start at zero; arbitrary sparse offsets; or fully sparse legends. Always-zero lessons permit `fixed_origin_pairs`. Arbitrary sparse offsets complicate parsing and exact controls without canonical evidence. Offset 0/1 is the smallest counterexample family.

**Probe.** The shifted witness is present in 300/600 semantic-gate draws and 24/48 exhaustive schedule rotations; `fixed_origin_pairs` is rejected in every complete lesson.

**Failure modes and limits.** Offsets greater than one and gaps inside the legend are not generated. The canonical scanner can handle some such cases, but this repair claims only compact offset-0/1 legends.

## D6 / R4 — Add one-step mapping chains

**Choice.** Chain profiles use `a→b, b→d` (with remaining pairs disjoint), and the official rule applies the map once.

**Original rationale.** Unknown. The baseline did not deliberately distinguish one-pass replacement from transitive/cascading replacement.

**Alternatives considered.** Only disjoint mappings; cyclic mappings; or longer chains. Disjoint mappings cannot refute cascade. Cycles make a naive cascade undefined or implementation-dependent. One-step acyclic chains are the smallest safe witness.

**Probe.** Mapping-chain witnesses occur in 300/600 semantic-gate draws and 24/48 exhaustive rotations; the `cascade_mapping` shortcut fits canonical pairs but is rejected by every complete generated lesson.

**Failure modes and limits.** Longer chains and cycles are outside the generated domain. The one-step case is sufficient to establish simultaneous, one-pass semantics.

## D7 / R4 — Preserve one unmapped control

**Choice.** `control_kind` is exact `none`, `target`, or `neutral`; scheduled lessons always include a target or neutral control, while exact overrides can request none.

**Original rationale.** The canonical rule preserves unmapped colors, but baseline lessons did not consistently teach that behavior.

**Alternatives considered.** Always no control; several controls; or only neutral controls. No control permits “erase everything else.” Multiple controls add placement interactions and can dominate the sparse body. Target-only and neutral controls cover both a mapped value that is not a source and an unrelated color.

**Probe.** Preserved-control witnesses occur in 600/600 semantic-gate draws and 48/48 exhaustive rotations; `erase_unmapped` is rejected.

**Failure modes and limits.** At most one control cell is generated and validated. Multi-cell or multi-color distractors remain out of domain.

## D8 / R2 — Use compact two-to-four-cell source components

**Choice.** Every source appears uniformly two, three, or four times in a 2×2-local 8-connected shape.

**Original rationale.** The baseline used textures/density controls whose relation to actual source structure was not exact.

**Alternatives considered.** Singletons; arbitrary density; long paths; independent counts per source. Singletons make source presence brittle and do not test replacement over components. Density is not an exact semantic control. Long paths and independent counts expand the grammar without adding a rival witness needed here.

**Probe.** Exact `source_uses` observation is checked for all 1,152 joint cases. Self-check rejects absent, oversized, and disconnected source impostors.

**Failure modes and limits.** Shapes are compact and counts are uniform across sources. The rule itself does not require either property; these are generator-manifold restrictions for reliable sparse lessons.

## D9 / R5 — Validate source components with 8-connectivity

**Choice.** Treat diagonal adjacency as connected.

**Original rationale.** The initial repair hypothesis used 4-connectivity; the canonical data disproved it.

**Alternatives considered.** Keep 4-connectivity and special-case the canonical input; remove connectivity validation; use one global source bounding box. A canonical exception would make the contract incoherent. No connectivity check would re-admit scattered impostors. A bounding box does not establish connectedness.

**Probe.** The first green attempt failed exactly one test because a canonical source is diagonal. The revised test and implementation pass all four canonical pairs and all generated shapes (`checks/tdd-green-1/result.json`, `checks/tdd-green-2/result.json`).

**Failure modes and limits.** 8-connectivity allows diagonal chains broader than the generated 2×2 shapes. This is intentional validator tolerance for canonical authority, not a claim that every accepted diagonal form is sampled.

## D10 / R2–R3 — Generate width 7–14 but accept canonical width 6

**Choice.** The exact `grid_w` override range is 7–14; `self_check` accepts 6–14.

**Original rationale.** Canonical data include width 6, while a three-pair offset-1 legend needs width 7.

**Alternatives considered.** Expose width 6 and mark many combinations incompatible; reject the canonical width-6 pair; or force legend offset 0 at width 6. Rejecting canonical authority is unacceptable. Conditional compatibility would make a simple exact Cartesian contract more complicated. Therefore generation starts at 7 and validation remains broader.

**Probe.** Every exact joint override combination is constructive with no incompatibility declarations, and all canonical inputs pass.

**Failure modes and limits.** Validator acceptance is intentionally broader than advertised generation for this single dimension. Callers cannot request width 6 through the exact override API.

## D11 / R2 — Make the Cartesian control space fully constructive and reject bad overrides

**Choice.** Declare no incompatible combinations; reject unknown keys, booleans masquerading as integers, out-of-range integers, and invalid enum values before generation.

**Original rationale.** Unknown. Baseline permissiveness caused silent ignored controls.

**Alternatives considered.** Coerce inputs; ignore unknown keys; or maintain an incompatibility table. Coercion and ignoring destroy reproducibility. The selected geometry can realize every legal combination, so incompatibility metadata would be unnecessary complexity.

**Probe.** Tests enumerate 288 combinations × four difficulty values. The override battery checks 29,070 draws and a bad unknown key.

**Failure modes and limits.** This is intentionally strict API behavior; callers must migrate rather than rely on silent fallback.

## D12 / R1 — Leave the Racket authority unchanged

**Choice.** Modify only the generator/tests/notes/workspace; do not change canonical data or the Racket rule.

**Original rationale.** The canonical transformation was already correct; failures were in sampling, validation, and teaching evidence.

**Alternatives considered.** Tighten the Racket rule to the new generator manifold or alter canonical examples. That would confuse task semantics with data-distribution policy and risk changing the reference task.

**Probe.** Rule smoke reports 120/120 parity, authority synchronization is green, and the declared rule hash remains `08068e7e2317`.

**Failure modes and limits.** The Python validator is stricter than the pure task rule. Accepted training inputs are a deliberate subset of all grids on which the Racket transform can execute.

## D13 / R5 — Retain a reusable authoring probe

**Choice.** Add `workspace/lesson_probe.py`, which imports the task declarations, verifies canonical-shortcut fit, checks all schedule starts/query rotations, and records witness coverage.

**Original rationale.** No prior reusable probe existed.

**Alternatives considered.** Encode only assertions in pytest; copy rival names into an external script; or rely solely on the sampled shared census. Pytest alone is less convenient for curriculum iteration. Copying declarations drifts. A sampled census does not enumerate every start of a short deterministic period.

**Probe.** A dedicated CLI test first reproduced a missing-runtime-path failure, then passed after bootstrap repair. Final JSON records 48 rotations, no ambiguity/shortcut failures, and all witnesses.

**Failure modes and limits.** The probe evaluates only declared competitors and witnesses. It explicitly does not prove uniqueness against every computable rule.

## D14 / R6 — Do not patch source around transient harness stalls

**Choice.** Preserve interrupted runs, retry the exact stage unchanged, and require one clean aggregate battery.

**Original rationale.** Not applicable; this was a review-process ruling.

**Alternatives considered.** Increase arbitrary internal timeouts, simplify generator logic without evidence, or report a collection of individual stage passes as an aggregate pass. Those would treat orchestration symptoms as source defects or overstate verification.

**Probe.** The same frozen source passed direct `rule_smoke`, `profile_floor`, and `grammar` retries, followed by the authoritative 12/12 aggregate run.

**Failure modes and limits.** The root cause of the runner stalls is not established. F2 proposes instrumentation rather than claiming a speculative fix.

## Rejected broadening

I did not add sparse multi-row legends, more than three mappings, arbitrary component topology, multiple controls, palette aliases, or undeclared heuristic rivals. Those may be useful in a future version, but adding them now would enlarge the lawfully generated manifold faster than the semantic and exact-override tests could justify.

## D15 / Parametric prototype — Choose one-step versus cascading legend application

**Choice.** Add a separate proposed `workspace/parametric/` family with one private, episode-fixed `mode`: `once` preserves the exact canonical Racket source, while `cascade` repeatedly follows source→target chains until a non-source (or a repeated color) is reached. The production generator and canonical authority remain unchanged.

**Why this parameter.** The existing generator deliberately includes mapping overlap, but canonical labels apply the legend once. A chain `a→b→c` therefore gives a compact, causally meaningful rule branch: an `a` body cell becomes `b` under `once` and `c` under `cascade`. Both settings share the same inputs, so demonstrations teach the executed transformation rather than a setting-correlated input distribution.

**Episode contract.** The adapter accepts 2–6 demonstrations and 1–4 queries independently. Retained episodes use four distinct query shapes (10×12, 16×20, 24×24, 30×30), alternate legal legend offsets 0/1, contain dense body content across the canvas, and expose only demonstrations plus query 1 through `first_turn()`. Public identifiers hash the exact visible bytes; settings, programs, seeds, answers, runtime/source bindings, and finite-rival certificates remain private.

**Evidence.** `tests/test_parametric_rewrite_mode.py` plus the unchanged target suite pass 60/60. Protected Racket replay verifies two retained three-demo/four-query episodes (14 stored labels and 28 cross-parameter executions), and the six-request probe covers both modes at 2, 3, and 6 demonstrations. The bounded adversarial surfaces are a shifted legend that defeats fixed-origin parsing and a substantive 30×30 input whose two Racket programs differ; both pass. Current source-bound inventory: `workspace/parametric/evidence/manifest.json`.

**Failure modes and limits.** The demonstration-only certificate compares eight declared one-step/cascade, placement, reversal, identity, and erasure rivals; it is not a uniqueness proof against arbitrary programs. The parametric sampler is deliberately denser and supports larger dimensions than the canonical production distribution. This is a proposed prototype only: it is not owner-accepted and is not admitted to training.
