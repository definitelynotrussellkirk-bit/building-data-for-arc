# Current notes: `928c39acebe3`

## Intended rule

A red `2` emits a ray to the right. Yellow `4` is a slash mirror (`/`), gray `5` is a backslash mirror (`\\`), and magenta `6` stops the ray without being painted. The output is an otherwise empty same-size grid with every traversed cell, including mirror cells, painted cyan `8`. The canonical Racket authority is unchanged and pinned by `RULE_HASH = "5e6d34fb1a87"`.

## Distribution decision

Version 2.0.1 replaces the previous nominal scalar axes and degenerate textures with one exact `scene_profile` axis. Four profiles reproduce the linked canonical shape/mirror sequences; two profiles exercise the canonical source gap: slash approached from west and backslash approached from north. `DEFAULT_SCHEDULE` alternates canonical and probe profiles over eight slots. A normal lesson uses three demonstrations and one query, so every four-pair window contains two probes and every single-query rotation leaves at least one probe visible.

Difficulty changes legal layout geometry through a band-specific RNG stream but does not change the rule or selected profile. Every scene has one source, both mirror types, multiple reflections, one terminating blocker, and all mirrors on the traced path.

## Reversed prior choices

The previous generator advertised eleven controls (`grid_h`, `grid_w`, counts, palette/density/position/texture fields) that were not an honest exact product. Those controls and degenerate outputs were removed. Unknown or invalid overrides now fail loudly; `observe_overrides()` reports the exact realized profile.

## Semantic evidence

The four canonical labels omit two mirror-direction branches. The strongest retained shortcut uses the canonical transition table but continues straight for slash-from-west and backslash-from-north. It fits all four labeled canonical pairs. The authority-checked generated counterexample is `counterexamples/unseen_direction_lookup.json`; the shortcut differs from Racket in 21 cells.

`workspace/reference_probe.py` is an independent authoring oracle and shortcut probe. Task-local tests cover the rule pin, canonical parity, exact controls, validation, schedule residues, all query rotations, declared witness/rival claims, structural mutations, RNG purity, live difficulty bands, and the retained counterexample.

Final measured evidence for generator SHA-256 `fab600af480571e33e42761999659614750de88c8f6f4ae7b783f17dac3fc3d1`:

- after battery: 12/12 stages green;
- portable task tests: 16/16 passed;
- semantic smoke: 12/12 lessons and 48/48 required rotations identifiable against declared rivals;
- source-bound census: 300/300 lessons, 1,200 pairs, 956 unique inputs, zero production or rotated ambiguities;
- Racket rule smoke: 120/120 valid applications and zero Python-mirror mismatches.

## Known limits and open findings

This is a deliberately bounded curriculum for one terminating source ray. It does not sample multiple emitters, loops, off-path mirrors, or malformed inputs even though the authority can define behavior for some of them. The finite rival suite does not prove unique induction against every possible coordinate-, profile-, or schedule-specific shortcut. New profiles should preserve exact observability and must be checked under every query rotation before entering the production schedule.
## Current reviewer considerations

Source SHA-256: `fab600af480571e33e42761999659614750de88c8f6f4ae7b783f17dac3fc3d1`.

# Design decisions for `928c39acebe3`

## Evidence basis

No prior return for the selected task was used as a measurement or copied as a repair. The selected task's associated-notes ledger was empty. Decisions were based on the pinned baseline source, all four labeled canonical pairs, the completed before battery, source-bound probes, and the synchronized Racket authority. Other repository generators were consulted only for public API and contract patterns, not as evidence about this task's semantics.

## D1 — Preserve the authority and pin it explicitly

**Prior state.** The generator had no `RULE_HASH`, even though the canonical authority was already synchronized and its smoke checks passed.

**Decision.** Keep the canonical Racket rule unchanged and set `RULE_HASH = "5e6d34fb1a87"` in the generator. Implement a pure Python `rule_mirror()` only as an authoring mirror and semantic-scoring hook.

**Reason.** The observed problem was the input/curriculum distribution and contract, not label correctness. Changing the authority would have widened scope without evidence.

**Probe.** The independent `workspace/reference_probe.py`, the production Python mirror, and all four canonical labels agree. Final rule smoke compared 120 generated inputs against Racket with zero mismatches.

**Failure mode / limit.** Two implementations can share a conceptual bug; the independent probe therefore uses separate code and the retained counterexample is additionally bound to a real Racket receipt.

## D2 — Replace eleven pseudo-controls with one exact composite axis

**Prior state.** The baseline advertised grid sizes, palette controls, counts, density, position bias, texture, and degenerates. Several were fixed, clamped, aliases, rejected repeatedly, or not observable from the returned grid.

**Decision.** Advertise only `scene_profile`, whose value fixes the observable grid shape and ordered mirror-hit sequence. Reject every unknown override and invalid profile instead of silently ignoring or clamping it.

**Reason.** A composite profile is the true jointly feasible semantic unit. Separate scalar axes would imply a Cartesian product the geometry cannot honestly realize.

**Alternative rejected.** Retaining scalar `grid_h`, `grid_w`, and `n_mirrors` with compatibility rules. That recreates a large sparse override surface, makes exact observability difficult, and invites silent coercion.

**Probe.** Focused tests request every profile in every difficulty band over four seeds, verify exact observation, deterministic fresh returns, legality, and oracle parity. The final override stage accepted all 630 planned draws with no findings.

**Failure mode / limit.** The axis is intentionally coarse. A downstream consumer needing independent geometry controls would require new, genuinely joint-safe profile families rather than resurrected nominal axes.

## D3 — Retain all four linked canonical profiles

**Decision.** Add four profile recipes matching the canonical linked signatures:

- `canonical_8x12_545`
- `canonical_9x13_554`
- `canonical_8x14_5454`
- `canonical_9x14_5544`

The signature links height, width, and the mirror colors encountered by the ray; it does not accept arbitrary recombinations.

**Reason.** The profile-floor gate and training distribution should remain anchored to every public shape/semantic pattern rather than merely the same palette.

**Alternative rejected.** Sampling shape and mirror sequence independently. Most cross-products are not represented by the canonical support and could make the strict profile claim misleading.

**Probe.** All four canonical inputs pass `self_check()` and `strict_canonical_like()`. The 60-draw profile floor recorded 21 exact hits and nonzero support in easy, medium, and hard.

## D4 — Add two full-direction semantic probes

**Decision.** Add compact 10×14 and wide 11×16 profiles whose one ray hits mirror colors `(5,4,4,5,4,5)` and necessarily includes slash-from-west and backslash-from-north.

**Reason.** The four labeled canonical pairs never exercise those two incoming-direction branches. The strongest source-bound rival can therefore use the canonical transitions but continue straight for precisely those unseen cases.

**Alternative rejected.** Add one isolated one-turn example for each missing direction. A single-turn scene would distinguish the lookup table but weaken evidence for following a long chain and honoring a blocker. The selected probe covers both omissions on one multi-reflection route.

**Probe.** `counterexamples/unseen_direction_lookup.json` is an exact 10×14 generated input. Racket and the independent probe agree on the intended output; the combined shortcut differs in 21 cells. Both individual direction shortcuts and the combined shortcut fit all four labeled canonical pairs.

**Failure mode / limit.** The probes cover the complete incoming-direction table for the two mirror types used by this task, but they do not exhaust multiple-ray interactions or loops.

## D5 — Use an alternating eight-slot lesson schedule

**Decision.** Alternate canonical-linked and full-direction profiles in an eight-slot period. A production lesson is any contiguous four-pair window, assembled as three demonstrations plus one query.

**Reason.** Every four-pair window then contains two direction probes. Under any single query holdout, at least one remains visible, so the demonstrations refute the partial lookup-table shortcut.

**Alternatives rejected.** Pure random profile choice can create a correct but ambiguous lesson. A schedule with only one probe per four pairs fails when that probe is held out as the query.

**Probes.** Focused tests enumerate all eight start residues, all three bands, eight seeds, and all four query positions. The semantic smoke passed 12/12 lessons and 48/48 rotations. The 300-lesson census passed all 1,200 query rotations.

**Failure mode / limit.** The shared semantic report currently labels schedule coverage `not_declared` because this generator exposes `SCHEDULE_PERIOD`, while the tool looks for a differently named optional declaration. The task-local exhaustive residue test supplies the missing bounded evidence.

## D6 — Keep difficulty semantic-neutral but geometrically live

**Decision.** Difficulty does not change the rule or profile schedule. It salts the layout RNG so easy, medium, and hard produce different legal nuisance geometry for the same selected profile.

**Reason.** The baseline's bands were effectively dead, but inventing difficulty-specific semantic rules would be unjustified. Geometry variation makes the band observable without changing what must be learned.

**Alternative rejected.** Vary mirror count by band. Mirror count is part of the profile's semantic signature and changing it independently would break exact profile overrides.

**Probe.** For every schedule slot, focused tests require at least two distinct grids across the three bands while preserving the same observed profile. Defect lint no longer reports dead bands.

**Failure mode / limit.** Difficulty remains a nuisance-variation label, not a calibrated reasoning-complexity scale.

## D7 — Enforce the intended curriculum domain in `self_check()`

**Decision.** Require a rectangular legal ARC grid, exactly one emitter and blocker, both mirror colors, all mirrors on the traced path, multiple reflections, a blocker termination, no loops, and no unrecognized nonzero cells.

**Reason.** Correct Racket labels are insufficient when generated examples contain stray objects or fail to exercise the claimed operation. The validator should state the actual training domain.

**Alternative rejected.** Permit off-path distractor mirrors. They can be lawful under the authority but encourage object-selection shortcuts and make profile observation ambiguous without adding evidence needed for this repair.

**Probe.** Mutation tests remove the source, blocker, or an on-path mirror; introduce illegal cells and ragged shape; all are rejected. The final self-check, grammar, distribution, and rule-smoke stages pass.

**Failure mode / limit.** This is a curriculum validator, not a full authority-domain validator. It intentionally rejects some inputs the Racket rule could process.

## D8 — Keep semantic scoring executable and independently inspectable

**Decision.** Declare seven witnesses, eight lesson rivals, three canonical-fitting shortcuts, witness-to-rival mappings, and a deterministic `lesson_identifiable()` hook. Build `workspace/reference_probe.py` as a separate implementation for tests and future agents.

**Reason.** Textual claims such as “uses both mirrors” do not establish that a lesson distinguishes plausible wrong rules. Executable rivals make the claim falsifiable and source-bound.

**Alternative rejected.** Compare only against generic image mutations. Those do not target the actual source gap: a partially learned direction table.

**Probe.** The final semantic gate reports all seven witnesses firing and all named rival claims holding. The larger census reports zero surviving declared rivals in production or rotations.

**Failure mode / limit.** The rival set is finite. Unlisted coordinate, profile-memorization, or schedule-specific rules remain possible; the reports must not be read as universal identifiability proof.

## D9 — Retain failures and a minimal authority-bound counterexample

**Decision.** Preserve the red test logs and the exact generated counterexample rather than only the final green reports.

**Reason.** The red logs establish that the regressions detect the baseline defect. The JSON fixture lets a future agent replay the precise disagreement, check generator arguments, inspect both outputs, and verify the authority binding.

**Probe.** Final test `test_retained_partial_lookup_counterexample_replays_and_refutes_combined_shortcut` regenerates the input, checks the saved Racket output, confirms all-canonical fit, and checks the exact 21-cell disagreement list.

## D10 — Stop at the selected-task boundary

**Decision.** Do not edit the two adversarial audit targets, shared check tools, canonical data, or Racket source. Put shared-tool suggestions in `FEEDBACK_TO_CODEX.md` and audit reproductions under `checks/audit/`.

**Reason.** The assignment permits source edits only under the selected generator. Separating repair, audit, and tooling feedback keeps the returned delta reviewable and prevents an audit from being mistaken for an approved repair.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-b03000a5ffc487ad:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `fab600af480571e33e42761999659614750de88c8f6f4ae7b783f17dac3fc3d1`. At disposition, audited bytes match the current source.

### Current decision

Reviewer-reported on unchanged source fab600af480571e33e42761999659614750de88c8f6f4ae7b783f17dac3fc3d1. No issue within the bounded scope. Sixteen portable tests and strict semantics pass. The unseen_directions_continue_straight rival fits all four canonical pairs but is refuted by the existing full_direction_probe_compact witness at seed=91/index=0/medium, differing in 21 Racket cells. The 300-lesson census has 1200 labelled pairs, 956 unique inputs and zero production/required-rotation ambiguities. The embedded full-battery summary is incomplete because only the audit preset was requested; no universal claim or new approval is made. Retain source-bound evidence: `checks/audit/928c39acebe3-combined/RUNTIME_MANIFEST.json` `checks/audit/928c39acebe3-combined/checks/928c39acebe3_audit_battery_summary.json` `checks/audit/928c39acebe3-combined/checks/928c39acebe3_audit_commands.jsonl` `checks/audit/928c39acebe3-combined/checks/928c39acebe3_audit_semantic_gate.json` `checks/audit/928c39acebe3-combined/checks/928c39acebe3_audit_semantic_gate.log` `checks/audit/928c39acebe3-combined/checks/928c39acebe3_audit_semantic_gate.ok` `checks/audit/928c39acebe3-combined/checks/928c39acebe3_audit_semantic_gate.receipt` `checks/audit/928c39acebe3-combined/checks/928c39acebe3_audit_summary.json` `checks/audit/928c39acebe3-combined/checks/task_tests.xml` `checks/audit/928c39acebe3-combined/progress.log` `checks/audit/928c39acebe3-combined/result.json` `checks/audit/928c39acebe3-lesson-census.json.gz` `checks/audit/928c39acebe3-lesson-census.summary.json` `checks/audit/928c39acebe3/inspection.json`

### Assessment or prior finding

## 928c39acebe3

**Conclusion: No issue found in the bounded audit.** The audited generator SHA-256 is `fab600af480571e33e42761999659614750de88c8f6f4ae7b783f17dac3fc3d1`; declared rule hash `5e6d34fb1a87`.

The strongest plausible canonical-fitting rival was `unseen_directions_continue_straight`: use the canonical mirror transitions for directions seen in the four canonical pairs, but continue straight when color 4 is approached from west or color 5 from north. It fits 4/4 labelled canonical pairs. The target already contains and emits an exact counterexample at `repo/generators/928c39acebe3/counterexamples/unseen_direction_lookup.json` (seed 91, sample index 0, medium, `scene_profile=full_direction_probe_compact`), where the rival differs from the Racket authority in 21 cells.

Checks performed:

- `checks/audit/928c39acebe3-combined/result.json`: 16/16 task-local tests passed and the strict semantic gate passed. The embedded battery object is intentionally incomplete because the `audit` preset ran only task tests plus semantic gate; the top-level audit result is the relevant completed verdict.
- `checks/audit/928c39acebe3-lesson-census.summary.json`: 300/300 lessons materialized (100 per band), 1,200 labelled pairs, 956 unique input grids, 0 production ambiguities, and 0 ambiguities across 1,200 required query rotations.
- `checks/audit/928c39acebe3/inspection.json`: source-bound summary, strongest rival, exact counterexample recipe, and limits.

The target was not modified. This finite audit covers declared rivals and schedule tests, not every possible coordinate-memorization or undeclared hypothesis.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
