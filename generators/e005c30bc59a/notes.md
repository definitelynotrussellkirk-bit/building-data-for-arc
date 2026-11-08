# Working notes: e005c30bc59a

## 2026-10-02 review repair

- Baseline objects were scattered independently. In the retained 768-draw census, only 140 draws (18.23%) reached any mirror, 8 (1.04%) reached two or more, and 76 (9.90%) put the source in a corner, making its inward direction ambiguous.
- All three canonical training demonstrations use source color 7. Therefore the strongest exact canonical shortcut is: trace the beam correctly but always paint 7. The final generator emits explicit non-7 cases and tests the rival as executable code.
- Replaced layout scattering with path-first construction. Ordinary draws now guarantee a reached mirror, a black segment before every event, a non-corner source, and wall/boundary termination; optional mirrors/walls are placed only off route.
- Added exact axes for dimensions, source edge/color, reached/decoy mirror profile, and wall profile. Removed fake palette/density/texture axes and unlawful degenerates.
- Added Python mirror/rivals, canonical shortcut declarations, semantic witnesses, and a four-example lesson-identifiability check.
- Canonical train case 1 legitimately revisits a cell from a new direction. Validation therefore detects loops by repeated `(row, column, direction)` state, not by repeated cell.
- An intermediate implementation timed out in the official override stage because hard role 3 retained its wall-stop mirror orientation after an explicit boundary `wall_profile` override. Explicit route-profile overrides now disable hidden role orientation constraints; the deadline regression, 605-case profiler, and final 54,450-draw official override stage pass.
- The canonical Racket program was not changed.

Reusable probes are documented in `workspace/README.md`: `beam_coverage_probe.py`, `shortcut_probe.py`, `override_contract_profiler.py`, and `audit_override_probe.py`. Imported associated notes remain in `evidence/associated_notes.jsonl`.

## 2026-10-03 crossing-curriculum repair

- The v3 source hash was `daa86d18a318ea6b6b7e4235b5f40d7df2923754149722c906afbb1b9bec1a2c`. It deliberately sampled only non-crossing routes even though the canonical rule permits revisiting a coordinate from a different direction.
- Strongest remaining canonical-fitting rival: trace source color, mirrors, and walls correctly, but stop before processing the first coordinate already visited. It matches all three canonical training demonstrations and the public test pair because the only canonical revisit is not followed by a newly paintable cell.
- A source-bound before probe over 100 disjoint four-example lessons per band found zero crossing witnesses and 100/100 rival-surviving lessons in easy, medium, and hard. Unique inputs were 395/400, 398/400, and 399/400 respectively; there were no generation or validation errors. Evidence: `checks/crossing_revisit_before_100_lessons.json`.
- Version 4 adds a default cyclic role with a right-edge source, three reached mirrors of kinds `(1, 2, 1)`, a perpendicular revisit, at least one newly painted cell after the revisit, a wall stop, and one off-route decoy mirror. The role is scheduled once in every four default examples. Explicit semantic overrides continue to use the generic route sampler so advertised exact controls remain authoritative.
- Added executable rival `stop_on_revisited_cell`, canonical-shortcut declaration, semantic witness `crossing_continues_after_revisit`, a lesson-level regression test, and reusable independent probe `workspace/crossing_revisit_probe.py`.
- The final source hash is `4cffc894fadae67da8d9102054d64545ed4f4d9e1ba8f11a7d4c42fbc3fb539d`. The 100-lesson-per-band after probe found exactly 100 crossing witnesses among 400 generated inputs in each band, zero failed lessons, and 25/25 rival-refuting lessons for each cyclic start residue. Unique inputs were 393/400, 396/400, and 399/400; there were no generation or validation errors, and the independent tracer matched `rule_mirror` on every input.
- The supported Racket runner confirmed the exact medium witness `seed=crossing-revisit-probe-v1:medium:0`, `sample_index=3`: intended output paints `[2, 9]` with 8 after revisiting `[3, 9]`, while the rival leaves `[2, 9]` black. The independent Python output equals Racket authority hash `9114178dd0f7`.
- The official after battery passed all 12 stages. The canonical Racket program and `RULE_HASH` were not changed.

Remaining limitation: the guaranteed crossing is a deliberate default lesson role, not a new override axis. Arbitrary explicit override draws remain lawful and semantically checked but are not individually guaranteed to contain the crossing witness.
## Current reviewer considerations

Source SHA-256: `4cffc894fadae67da8d9102054d64545ed4f4d9e1ba8f11a7d4c42fbc3fb539d`.

# Decisions — e005c30bc59a

## D1 — Target the strongest surviving rival

**Choice.** Repair the rule-identification gap represented by `stop_on_revisited_cell`: trace the source color, mirrors, and walls correctly, but halt before processing the first coordinate already visited.

**Why.** This rival is semantically close to the intended rule, fits all canonical public pairs, and exploited a specific distribution mismatch: the canonical rule permits coordinate revisits, while the frozen generator deliberately sampled non-crossing routes. A 100-lesson-per-band baseline probe measured zero counterexamples.

**Rejected alternatives.** More superficial shortcuts such as constant trail color 7 were already covered by v3. Adding more random colors or distractors would not distinguish coordinate-based loop detection from directional-state loop detection.

**Failure mode addressed.** A learner could infer that any painted coordinate is an obstacle or loop boundary and still score perfectly on the old curriculum.

## D2 — Guarantee one witness per default four-example lesson

**Choice.** Reserve cyclic role 3 for a crossing-and-continue route in every difficulty band. The other roles retain edge, palette, mirror, wall, boundary, and distractor coverage.

**Why.** A low-probability random crossing would improve aggregate frequency without guaranteeing that an individual lesson teaches the distinction. A fixed cyclic role makes the lesson contract deterministic and affordable to test at every start residue.

**Rejected alternatives.** Making every draw self-crossing would distort the task distribution. Sampling crossings probabilistically would leave rival-surviving windows. Increasing `EXAMPLES_NEEDED` would make the lesson larger without solving the witness guarantee.

**Limitation.** The guarantee applies to default cyclic lessons. Explicit overrides remain exact and may bypass the special route.

## D3 — Use a simple three-mirror hook

**Choice.** The witness route starts at the right edge and reaches mirror kinds `(1, 2, 1)`. It forms a rectangular hook, crosses the initial horizontal segment while traveling north, continues through at least one fresh black cell, and then stops at a wall. The role uses `three_hit_one_decoy` and `wall_stop_plus_decoy`.

**Why.** Three turns are the smallest clear construction that returns a ray across an earlier segment without repeating a directional state. A wall gives a bounded, visibly checkable continuation. The decoy retains the lesson that only encountered objects matter.

**Rejected alternatives.** A crossing followed immediately by a wall would not refute the rival—the canonical examples already demonstrate that failure. A free-form rejection sampler for arbitrary crossings would be harder to reason about and could regress override performance.

**Failure modes considered.** The helper asserts one repeated path coordinate, at least one fresh cell after it, no repeated directional state, and an in-bounds wall. Standard `self_check`, independent tracing, semantic-gate checks, and Racket comparison provide additional layers.

## D4 — Preserve override authority instead of adding a crossing axis

**Choice.** Use the crossing helper only for the exact default role-3 profile. Any explicit route-profile override continues through the generic sampler.

**Why.** Existing axes are advertised as exact controls. Secretly forcing a crossing under incompatible overrides would violate those contracts and reintroduce the kind of override regression repaired in v3.

**Rejected alternative.** A new `crossing=true|false` axis was unnecessary for teaching the default lesson and would enlarge the official override matrix and public surface.

## D5 — Make the shortcut executable and independently measurable

**Choice.** Add the rival to `LESSON_COMPETITORS`, `SEMANTIC_RIVALS`, and `CANONICAL_SHORTCUTS`; add witness `crossing_continues_after_revisit`; add lesson-level tests; add `workspace/crossing_revisit_probe.py` with an independent tracer.

**Why.** Narrative claims are fragile. Executable declarations let the semantic gate test the contract, while the independent probe avoids validating the generator solely against its own mirror implementation. The probe records final source hash, canonical hash, seed policy, unique-input counts, cyclic starts, disagreements, and exact witnesses.

**Rejected alternative.** Testing only that a generated path contains a duplicate coordinate would be insufficient: the route must visibly paint a new cell after the revisit, and the rival must actually disagree.

## D6 — Leave Racket authority unchanged

**Choice.** Keep canonical rule hash `9114178dd0f7`.

**Why.** The Racket rule already implements the intended behavior. The defect was solely in generated input coverage. The exact witness was checked through the supported Racket runner and matched the independent Python trace.

## D7 — Stop after finite but broad evidence

**Choice.** Use 100 disjoint lessons per band, cycle all four schedule starts, retain exact Racket evidence, run the complete official battery, and perform the required fresh solve.

**Why.** This meets the packet's requested scale while keeping the claim bounded. Results are reported as sampled evidence, not universal proof.

**Remaining uncertainty.** The structured witness family does not explore every possible crossing geometry, and masked post-repair solve labels are intentionally unavailable.
