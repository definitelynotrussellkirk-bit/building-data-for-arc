# Working notes: 2f0a4d589c58

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-03 review — counterfactual occlusion schedule

### Root cause

The inherited six-phase schedule covered useful semantic branches but coupled every geometry tuple to exactly one occluder. The task-local geometry-only rival therefore matched 1,200/1,200 sampled grids and survived all 300/300 three-demo lesson windows. The ordinary gates did not model this conditional correlation.

### Repair

- Version `3.0.0` → `3.1.0`.
- Adjacent indices now form minimal pairs: same dimensions, thicknesses, positions, horizontal color, and cyclic color offset; opposite occluders.
- Pair palettes come from source-stable RNG keyed by seed/pair/band and are still recorded through `GenCtx` for exact override provenance.
- The pre-repair geometry lookup is retained as `LESSON_COMPETITORS["geometry_only_occluder"]`.
- New regression: `tests/test_counterfactual_schedule.py`.
- Reusable source-bound census: `workspace/geometry_occlusion_probe.py`.

Final probe over 100 consecutive lessons per band: rival accuracy 50%, 0/100 windows survive per band, and 100/100 windows per band contain a same-nuisance/opposite-occluder demo pair.

### Authority repair

The selected `target_code` had the canonical semantics and normalized hash but not exact canonical text. It now equals canonical `program_solution` byte-for-byte. The older executable `raw_code` is retained unchanged as archival provenance. `RULE_HASH` remains `70d63db0a1f2`; after battery authority status is `selected_synchronized_archival_divergent`, execution parity PASS.

### Limits

The pair guarantee is tied to shared-seed consecutive-index lesson assembly. The finite geometry/size schedules remain intentional; this review disproves the measured occluder shortcut but does not claim universal shortcut freedom.

## Maintainer correction after intake

The returned paired schedule passed the generic battery but failed the frozen
three-demo identifiability test: adjacent single-cell geometry groups left
`single_cell_overlap` alive before a multi-cell query. Version 3.1.1 reorders
geometry phases as 0,2,1,3,4,5, retaining all six geometries and paired occluders
while separating the two single-cell groups. The original return and failed
test receipt remain intact. Fresh staged checks qualify these changed bytes.
## Current reviewer considerations

Source SHA-256: `62763719c9c6556fe64fdc0184eba3af744bb81faed1a90931edb17c3937fc99`.

# Decisions: 2f0a4d589c58

## M1 — reject invalid public controls at the source boundary

**Decision.** Validate `seed`, `sample_index`, `difficulty`, and overrides before they reach schedule arithmetic, RNG helpers, or `GenCtx`. Integer controls use `type(value) is int`, so `bool`, float, and numeric strings cannot enter silently. Categorical controls require exact strings from their declared domains. `None` remains the supported “use the scheduled/default value” sentinel.

**Why.** The baseline defect lint produced 153 strict-scalar findings, including `vertical_color_offset=8.75`, noninteger seeds/indices, negative indices, and Boolean integer overrides. Silent coercion makes provenance unreliable and can create examples outside the declared axis domain.

**Alternatives rejected.** Coercing with `int(...)` preserves the bug; validating only inside draw helpers leaves `schedule_profile` inconsistent; validating just the one observed axis would leave the same class of defect on the other controls.

**Probe.** `tests/test_strict_controls.py`, `checks/strict-controls-red.log`, `checks/strict-controls-green.log`, and the final defect-lint stage.

## M1 — keep version `3.1.1`

**Decision.** Do not bump the generator version.

**Why.** All accepted valid calls retain the same schedule, RNG keys, grids, and outputs. The change only rejects calls that violated the already-declared control contract. A version bump would imply a new valid data distribution and unnecessarily perturb source-stable RNG keys that include `VERSION`.

**Limitation.** Downstream callers that relied on accidental coercion now fail explicitly; that is intentional compatibility breakage at an invalid API boundary.

## M1/M3 — preserve canonical Racket authority and lesson schedule

**Decision.** Do not edit the selected Racket program, canonical ledger, rule hash, or counterfactual schedule. `RULE_HASH` remains `70d63db0a1f2`.

**Why.** Rule smoke, semantic, authority, and production lesson evidence were green. The observed defect was Python control validation, not task semantics. The ordered production census found 0 ambiguities in 300 lessons, and the geometry rival survived 0/300 ordered windows.

**Alternative rejected.** Changing schedule phases solely to force every synthetic hold-one-out rotation green would expand this review from a boundary fix into a curriculum redesign and could disturb a measured-good ordered policy.

## M3 — state the ordering contract rather than claim rotation support

**Decision.** Treat the lesson as an ordered curriculum: three demonstrations followed by the fourth pair as query. Report both results: 0/300 production ambiguities and 48/1,200 ambiguous synthetic rotations.

**Why.** The return guide explicitly distinguishes ordered-production evidence from query-rotation evidence. Suppressing the rotation failure would overclaim; treating it as an automatic canonical rejection would erase the valid production contract.

**Limitation.** A consumer that independently shuffles which pair is queried can receive an underdetermined lesson at the measured 4% rate for the declared geometry-only rival. Such consumers must either preserve ordering or request a future schedule redesign.

## M2 — one small episode-level parametric axis

**Decision.** Build a proposed `depth_policy` parameter with values `toggle`, `horizontal_front`, and `vertical_front`, drawn once per episode. The canonical default returns the source text byte-for-byte; variants replace one guarded overlap-color expression only.

**Why.** This preserves the original reasoning object (two crossing bars and overlap depth), changes no input constraints, and gives a compact three-way family whose settings are visibly distinguishable in three demonstrations.

**Alternatives rejected.** Parameterizing geometry or palette would vary nuisance factors rather than the rule. Adding multiple simultaneous rule parameters would create avoidable identifiability and attribution problems. Editing production `generate` would conflate an authoring prototype with the canonical repair.

**Probe.** `tests/test_parametric_depth_policy.py` and `checks/parametric/depth-policy-v1/report.json`; 3 settings, 3 episodes, and 36 protected-Racket evaluations.

## M4 — leave the inherited frozen portable test unchanged

**Decision.** Do not repair `tests/test_generator_2f0a4d589c58.py` in this return.

**Why.** The task instructions identify it as a frozen inherited fixture. Its fixed `parents[...]` canonical path is a portability problem, but changing it would mix historical test migration into the generator repair. The task-local tests use portable paths and were executed directly.

**Evidence.** `checks/task-tests/result.json` records preflight exit 2 before pytest; `checks/task-local-focused-tests.log` records 41/41 direct passes.

## A1/A2 — audit targets remain untouched

The audit assignment was inspection-only. `d3ae93aa8d37` has a reproduced single-episode straight-row ambiguity; `e93047bc5081` has a task-validator false acceptance for a Boolean cell plus ignored metadata, while the shared `apply` boundary rejects the malformed grid. Both exact assigned source hashes were preserved and no audit-target patch is included.
