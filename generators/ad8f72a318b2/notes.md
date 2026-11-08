# Working notes: ad8f72a318b2

## Intended rule

The input is exactly 11×9. A left-aligned unary prefix of blue cells in row 0 selects one of four 4×4 monochrome connected shapes. Row 0 column 5 selects identity, clockwise, 180°, counter-clockwise, or left-right reflection. Row 0 column 7 is the target color. Crop the selected shape to its nonzero bounding box, apply the transform, and recolor its foreground. The synchronized canonical Racket program remains the label authority; the Python mirror is for tests and semantic diagnostics only.

## Review-c93e93cd8c8f2433 decisions

- **Reversed random padding.** Version 2.1.1 emitted larger-than-canonical grids while its metadata claimed fixed 11×9. Version 3.0.0 returns the canonical 11×9 layout for every draw. Evidence: `checks/before/` versus `checks/after/`.
- **Removed dead controls.** Palette and texture declarations that did not alter returned pixels were removed. The exact public axes are now `index`, `transform`, and `target_relation`; unknown overrides fail rather than being silently ignored.
- **Broadened the target-color relation.** The prior generator always chose a target color absent from all panels, allowing a “unique control color” shortcut. The deterministic schedule now covers `absent`, `selected`, and `unselected` relations in every five-demo production window.
- **Made geometry diagnostic.** Each panel is connected, has 4–7 cells, is pairwise distinct from the other panels under the full dihedral group, and yields five distinct supports under the five advertised transform codes. A cached exhaustive 4×4 shape-class pool replaced a slow rejection loop.
- **Made lessons rotation-safe against declared rivals.** Five demonstrations are drawn from a 60-profile schedule. Global selector/transform mappings and the preserve-source-color rival are falsified in production order and under every tested query rotation. Code-specific rivals were rejected because a rotated query could hold out their only affected code.
- **Strengthened validation.** `self_check` rejects malformed controls, stray separator pixels, empty/disconnected/non-monochrome panels, duplicate panel colors, and invalid control relations. `observe_overrides` recovers every exact axis from pixels.
- **No authority change.** `RULE_HASH` is pinned to `5d4b4a902077`; canonical pairs still match the Python mirror and Racket smoke/authority checks pass.

## Verification and limits

Final generator SHA-256: `7639adca17bc2bd08b9ac74df221e5674dd476ed055dacaf6874562eeb7149d3`.

The final battery is 12/12 green; task-local tests are 9/9 green. A 300-lesson source-bound census materialized 1,800 unique pair inputs and found 0 production ambiguities and 0/1,800 ambiguous query rotations against the declared rivals. The focused suite additionally checks all 60 cyclic starts in all three difficulty bands and every one of six possible query positions.

These are finite tests against declared hypotheses, not a proof of unique induction against every possible rule. Generated shapes remain restricted to connected 4×4 supports of area 4–7, matching the intended panel envelope. Difficulty changes the shape-area pool but not the symbolic rule. No unresolved task-local blocker remains.
## Current reviewer considerations

Source SHA-256: `7639adca17bc2bd08b9ac74df221e5674dd476ed055dacaf6874562eeb7149d3`.

# Decisions for ad8f72a318b2

## D1 — Restore the canonical fixed frame

**Prior choice:** version 2.1.1 added random bottom/right padding even though its summary, invariants, and canonical examples described 11×9.

**Decision:** emit exactly 11×9 and retain the canonical control/panel coordinates.

**Why:** padding was not part of the authority, made `grid_h`/`grid_w` overrides non-exact, and introduced a cheap “ignore padding” nuisance rather than a useful generalization.

**Rejected alternative:** advertise variable dimensions and teach padding removal. That would broaden the task beyond its canonical semantics and still require changing metadata, validators, and lessons.

**Probe:** fixed-shape assertions in the task tests plus final override/profile-floor stages.

## D2 — Keep only observable semantic axes

**Decision:** public axes are `index`, `transform`, and `target_relation`. Unknown overrides raise `ValueError`; every exact value is recoverable through `observe_overrides`.

**Why:** old palette/texture declarations were dead, aliases, or negative fixtures inside the ordinary domain. An axis that cannot be recovered from pixels is misleading training metadata.

**Rejected alternative:** retain compatibility aliases. Silent aliases make matrix coverage look broader than the actual input distribution and caused the baseline override failures.

**Failure mode / limit:** difficulty is intentionally not an advertised exact axis; it changes shape-area sampling but not the rule.

## D3 — Collide target-color roles

**Prior choice:** the target color was always absent from every panel.

**Decision:** schedule three relations—target absent, target equals the selected panel color, and target equals an unselected panel color.

**Why:** canonical examples permit these relations, and the old restriction let a learner identify the target as the unique header color without understanding the control role.

**Rejected alternative:** randomize relations independently. A deterministic 60-profile schedule guarantees each complete five-demo lesson contains all three rather than merely achieving population-level frequency.

**Probe:** all 60 cyclic starts are checked; the preserve-selected-color rival must be refuted.

## D4 — Use a complete cached shape-class pool

**Decision:** enumerate connected 4×4 supports of the band’s allowed areas, discard supports that do not distinguish all five transforms, canonicalize by D4, and sample four distinct classes with random orientations.

**Why:** this guarantees meaningful transform controls and pairwise panel distinction. Caching makes generation fast after one small finite enumeration.

**Rejected alternative:** per-grid rejection sampling. It could spend thousands of attempts, timed out a diversity run, and gave no completeness guarantee.

**Limit:** the pool covers the intended 4×4, area-4–7 envelope; it does not attempt arbitrary larger shapes.

## D5 — Five demonstrations, period 60

**Decision:** `EXAMPLES_NEEDED = 5`; controls advance modulo 4, 5, and 3 over a 60-profile period.

**Why:** any five consecutive production demonstrations cover every selector, every transform, and every target relation. This is the smallest straightforward window that shows all five transform codes.

**Rejected alternative:** fewer demonstrations. Four examples cannot directly exhibit five transform codes, leaving at least one code’s meaning unsupported.

**Query policy:** production is ordered, but the declared contract is also safe for any of the six materialized pairs to be the query. The focused suite checks all starts/bands/query positions; the 300-lesson census checks 1,800 rotations.

## D6 — Prefer global rivals over single-code rivals

**Prior intermediate choice:** rivals changed only one selector or transform code.

**Decision:** use shifted/reversed selector mappings, shifted/ignored/swapped transform mappings, and preserve-source-color.

**Why:** a single-code rival can survive when that code is the held-out query. Global or paired mappings are both plausible and falsifiable by the remaining demonstrations.

**Evidence:** the intermediate rotation test failed (`checks/red-rotation-tests/result.json`); the revised exhaustive rotation test and required gate pass.

## D7 — Preserve Racket authority

**Decision:** do not change the canonical program; pin `RULE_HASH = "5d4b4a902077"` and use a Python mirror only for local tests/rivals.

**Why:** canonical labeled pairs agree with the intended selector/crop/transform/recolor pipeline. The defects were entirely in input distribution, metadata, validation, and lesson construction.

**Failure mode:** future authority changes must invalidate the pin and rerun canonical mirror, smoke, and authority-sync checks.
