# Working notes: f41ae450c30b

## Review `review-4955a8d54ae6bb80`

The retained audit `review-3698d4252a1cb7a7:v0001` was used only as a lead. It identified inert controls, unknown-key acceptance, and a possible unsafe fallback on source hash `290f15a3a8027ad496e80f1ff832d986fb11d02d2dac3d1a054fadcf6e5b9707`. All claims below were remeasured against the packet baseline.

### Reproduced defects

- The before battery had 7 green, 2 advisory, and 3 failed stages (`lint`, `defect_lint`, `override`). The override stage recorded 5,936 findings over 59,940 draws / 666 cases and accepted an unknown key.
- A 1,500-draw independent baseline probe found a genuine third-object occlusion witness in only 79 inputs. Merely having both `0` and `8` in the matrix did not establish blocking because most nonvisible pairs were simply unaligned.
- The old 80-attempt fallback could return a final layout without proving the claimed visibility mix.
- All four canonical pairs were also solved by the blocker-blind rival `alignment_ignores_blockers`.

### Selected repair

Version `3.0.0` replaced the probabilistic layout search with constructive layouts. Every ordinary input contains a separated collinear triple with two clear adjacent rays and one blocked outer ray. The only advertised controls are the three controls that are exact, legal in every band, and recoverable from the grid: six named shape profiles, `n ∈ {3,4}`, and horizontal/vertical layout axis. Unknown, invalid, and wrongly typed overrides fail before generation. `RULE_HASH` is pinned to `8601bafc35ff`; the Racket source is unchanged.

The module now exposes independent structural validation, exact control observation, a Python rule transcription, an explicit blocker-blind rival, and a witness-to-rival contract. Focused tests and `workspace/reference_probe.py` provide source-bound regression and distribution evidence.

### Final measurements

- Generator SHA-256: `1302b515ef29e923bfb242e9d56a826c0fd2bdfd4fabb22c6288a0205a19d0c2`.
- Battery: all 12 stages green.
- Selected task tests: 11 passed.
- Independent probe: 750/750 samples deterministic, valid, exactly observable, witness-bearing, and rival-refuting; direct Racket parity 100/100.
- Source-bound lesson census: 300/300 lessons materialized, 0 ambiguous for the declared rival, 1,200 unique inputs; the rival fits all 4 canonical pairs and was refuted in all 100 lessons per band.

### Limits

This is finite declared-rival evidence, not a proof of universal induction. The construction intentionally narrows component shape to canonical-compatible dominoes. A secondary `adjacent_order_only` rule fits every generated `n=3` sample and some `n=4` samples, but fits 0/4 canonical pairs; across 9,000 default draws it agreed on 3,712 while 11 distinct intended graph signatures appeared in every band. Future expansion can add other canonical-compatible shapes and additional noncanonical rivals without weakening the guaranteed blocker witness.
## Current reviewer considerations

Source SHA-256: `1302b515ef29e923bfb242e9d56a826c0fd2bdfd4fabb22c6288a0205a19d0c2`.

# Decisions for f41ae450c30b

## Evidence discipline and prior lead

I preserved the packet baseline and used retained review `review-3698d4252a1cb7a7:v0001` only as a lead. That return named inert overrides and suspected the old fallback; its source hash equals this packet baseline (`290f15a3a8027ad496e80f1ff832d986fb11d02d2dac3d1a054fadcf6e5b9707`). I independently reran the complete before battery and a separate 1,500-draw probe before selecting a repair.

The before battery measured 7 green, 2 advisory, and 3 failed stages. The independent probe found only 79 genuine blocker witnesses in 1,500 draws, even though the old code aimed for mixed visible/nonvisible pairs. The distinction mattered: a nonaligned pair creates a `0` but does not teach that a third object blocks an otherwise valid ray.

## D1 — Keep the canonical Racket authority unchanged

**Choice.** Pin `RULE_HASH = "8601bafc35ff"` and repair only the generator, tests, and task-local tools.

**Rationale.** The canonical rule correctly solved all four examples and the defect was lesson construction/contract honesty, not rule execution. Rule smoke, grammar, Racket lint, and authority sync were already green before repair.

**Alternative rejected.** Editing the Racket rule would create unnecessary authority risk and would not fix the missing blocker examples.

**Probe.** Final rule smoke applied 120/120 grids with 120/120 Python-mirror agreement; authority sync reports execution parity `PASS`.

## D2 — Construct a blocker witness instead of searching probabilistically

**Choice.** Build a horizontal or vertical collinear triple `A–B–C` with spacing 2 or 3. Adjacent pairs have clear rays; the middle component blocks the outer pair. For `n=4`, add a separated fourth domino only after rechecking the teaching relation.

**Rationale.** This makes the semantic obligation true by construction and eliminates the old 80-attempt fallback, which could return a layout without proving its claimed invariant.

**Alternatives rejected.** Increasing the old retry count would only reduce, not remove, failure probability. Checking for both `0` and `8` in the output was rejected because nonalignment can supply the `0`. Hand-selecting a few fixed grids was rejected because it would reduce diversity and control coverage.

**Probe.** The semantic gate found `third_component_occlusion` in 600/600 draws. The independent audit found it in 750/750 draws. The 300-lesson census refuted `alignment_ignores_blockers` in every lesson.

## D3 — Shrink public controls to exact, observable semantics

**Choice.** Advertise only `scene_profile`, `n`, and `layout_axis`; reject unknown keys, invalid values, booleans masquerading as integers, and wrong types before drawing.

**Rationale.** The baseline advertised controls it did not consume and accepted typoed keys. A small truthful interface is more useful than a broad decorative one.

**Alternatives rejected.** Retaining palette, density, and position controls as “diagnostic” would leave them nonsemantic. Adding structured incompatibilities was unnecessary because every legal combination of the three retained controls can be constructed in every band.

**Probe.** The final override stage accepted 3,510/3,510 draws across 39 cases and 3 bands, with zero findings and unknown-key rejection. Focused tests cross every profile × `n` × axis combination in every band.

## D4 — Use named shape profiles rather than independent height/width ranges

**Choice.** Define six exact profiles: `7×10`, `8×11`, `8×12`, `9×12`, `10×14`, and `12×16`. The first four provide canonical-size support; the latter two retain larger scenes.

**Rationale.** Independent dimensions created band-specific rejection and made exact observation harder. Named profiles guarantee legal geometry and allow dimensions to recover the requested value exactly.

**Alternative rejected.** Keeping `grid_h` and `grid_w` as independent axes would require a larger compatibility matrix and would reintroduce impossible or poorly supported combinations.

**Probe.** Profile floor accepted all 4 canonical inputs and hit 35/60 exact/envelope profiles. The independent 750-sample crossed-control audit exercised all six profiles in every band with no observation mismatch.

## D5 — Restrict ordinary components to separated, distinct-colored dominoes

**Choice.** Use 3–4 two-cell 4-connected components, colors from `{1,2,3,4,5,6,7,9}`, and one-cell 8-neighbor separation.

**Rationale.** Dominoes match the canonical structural manifold accepted by `strict_canonical_like`, make the line-of-sight witness unambiguous, and keep output identity/color ordering visible. Excluding cyan avoids collision with the matrix edge color.

**Alternatives rejected.** Random 2–3-cell walks made construction and exact axis observation harder. Same-color components would create identity ambiguity. Allowing touching components would merge them under the rule’s 4-connectivity extraction.

**Limitation.** This is narrower shape diversity than the old random-walk generator. Future work can add other canonical-compatible component shapes after preserving exact controls and a guaranteed blocker witness.

## D6 — Make control observation and validation executable

**Choice.** Add `analyze_grid`, `self_check`, `strict_canonical_like`, and `observe_overrides`. Observe profile from dimensions, `n` from extracted components, and layout axis from the orientation of the three witness dominoes.

**Rationale.** Exact-control claims need an independent returned-grid observation, not only draw provenance. A pure analyzer also centralizes malformed-grid checks.

**Probe.** Focused tests cover malformed/unknown overrides, determinism, fresh returns, global-random isolation, separated dominoes, canonical acceptance, and exact round-trips. The final selected-task run reports 11 passed.

## D7 — Declare the canonical-fitting rival and bind it to a witness

**Choice.** Implement `alignment_ignores_blockers`, expose it through all three rival declarations, and bind `third_component_occlusion` through `WITNESS_RIVALS`.

**Rationale.** All 4 canonical pairs fit this shortcut, making it the central identifiability risk. An executable rival/witness pair lets the shared semantic and lesson tools test the claim instead of relying on prose.

**Exact witness.** `checks/question-shortcut/counterexample.json` records seed `424242`, the live Racket output, the rival output, and the two disagreement cells.

## D8 — Add an independent reusable probe

**Choice.** Add `workspace/reference_probe.py`, implemented without generator-private geometry helpers, with optional mandatory Racket parity.

**Rationale.** Generator self-checks can share the same bug as generation. The probe independently extracts components, sorts them, computes visibility, observes controls, and scores the rival.

**Probe result.** At 250 samples per band: 750 distinct inputs, zero self-check errors, nondeterminism, solver mismatches, observer mismatches, missing witnesses, or rival agreements. Direct Racket parity passed 100/100.

## Failed and intermediate attempts retained

- The first new tests failed 8 of 9 cases against the baseline, establishing the missing behavior before implementation.
- The first repaired tests passed 9/9. Adding the reusable probe brought the final selected suite to 11/11.
- Initial lint rejected computed AXES domain expressions because its analysis is static; literal equivalent domains fixed that without changing behavior.
- A one-stage profile run completed its substantive report but its wrapper did not terminate. It remains under `checks/preflight-profile/` and is not claimed as a pass.
- The first full after attempt was transport-interrupted after three green receipts. It remains under `checks/after/`; the completed rerun is `checks/after-final/`.

## Remaining limits and self-review

Finite declared-rival testing does not prove universal induction, and the census does not rotate every pair into every query position. A secondary `adjacent_order_only` rival fits 0/4 canonical pairs but agreed with 3,712/9,000 generated examples; all 2,252 sampled `n=3` cases have the path pattern. The same sample contained 11 distinct intended graph signatures in each band, and the canonical demonstrations themselves refute that rival. This is documented rather than silently promoted to a proven-complete competitor set.
