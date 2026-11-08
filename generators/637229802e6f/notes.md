# Working notes: 637229802e6f

## Current contract

The selected rule is source-bound and finite: in a 4×4 input, exactly one red cell (`2`) marks one of four 2×2 quadrants. The output is the corresponding all-red quadrant on magenta (`6`) background. Non-`{2,6}` cells are answer-irrelevant decorations. The canonical normalized rule hash is `315e7341b297`; generator version `4.0.0` pins it and declares the exact four-grid output codomain.

All lawful generated inputs use one of the four decoration profiles observed in the canonical labeled set: `(3 cells, 3 colors)`, `(4,4)`, `(7,4)`, or `(7,6)`. Decoration colors may use every legal non-`{2,6}` ARC color, including `0`. Grid size is intentionally fixed at 4×4 because that is the complete selected source domain; the removed `grid_n` range was unsupported metadata rather than real coverage.

## Reproduced baseline defects

The selected v3.2 source advertised controls it did not honor, omitted `RULE_HASH`, generated palettes that could not reach the canonical six-color profile, accepted minimal impostors, made easy/medium/hard byte-identical, lacked executable semantic evidence, and scheduled quadrants with `(seed + 2*sample_index) % 4`. That schedule visited only two of four branches for a fixed seed. The retained minimal witness is `counterexamples/two-quadrant-schedule.json`; before evidence is under `checks/before/`.

The initial full before battery was interrupted after retaining stage evidence. Its decisive failures were independently reproduced in focused checks; it is not reported as a completed aggregate pass.

## Decisions

### D1 — Replace broad-looking dead controls with exact source-bound axes

**Prior choice.** The imported generator exposed `grid_n`, free decoration counts/palettes, texture-like controls, and a quadrant bias although generation had effectively collapsed to the canonical 4×4 case.

**New choice.** Expose only `marker_quadrant`, local `marker_slot`, and `decoration_profile`. Every Cartesian combination is legal, generated exactly, and recoverable from pixels through `observe_overrides`.

**Reason and probes.** This makes the API truthful and prevents metadata from implying unsupported training support. The task tests exhaust all `4 × 4 × 4 = 64` combinations; the portable override gate is green. The failure mode is deliberate narrowness: this generator does not claim odd sizes, other split locations, multiple red markers, or decoration profiles absent from the selected source.

### D2 — Match all four canonical decoration profiles exactly

**Prior choice.** Decorations were too sparse and the palette excluded color `0`, so canonical palette/profile support was unreachable.

**New choice.** Sample exact `(cell count, distinct-color count)` profiles `(3,3)`, `(4,4)`, `(7,4)`, and `(7,6)` from colors `(0,1,3,4,5,7,8,9)` while keeping the unique red marker separate.

**Reason and probes.** All canonical labeled inputs pass both validators, all generated inputs are strict, profile-floor and distribution gates are green, and 600/600 semantic-gate samples were strict. Decorations remain randomized within the declared profile; no claim is made that this exhausts every lawful spatial arrangement.

### D3 — Teach both quadrant bits in every three-demo lesson

**Prior choice.** `(seed + 2*sample_index) % 4` alternated between two quadrants, leaving one independent left/right or top/bottom bit untaught.

**New choice.** Use `(seed + sample_index) % 4`, declare `LESSON_SCHEDULE_PERIOD = 4`, and use `EXAMPLES_NEEDED = 3`. Any three consecutive branches contain both row halves and both column halves. Within each aligned four-answer block, decoration profile and local marker slot are held constant, preventing those nuisance controls from labeling the quadrant.

**Reason and probes.** The retained counterexample is test-covered. `lesson-census.json` materialized 300 lessons (100 per band), 1,200 pairs, and 1,200 query rotations with zero ambiguity, warnings, or scoring errors. `schedule-period-s0.json` exhausts all four start residues and all query positions at seed 0 across all bands: 12 lessons, 48 rotations, zero ambiguity. `workspace/probe_contract.py` independently repeats the 48 finite schedule cases without Racket.

**Limit.** These checks refute the declared constant-quadrant and row-only/column-only rivals; they do not prove unique induction against every possible program. Fixed-seed period enumeration is finite evidence, not a claim about all seeds. The three difficulty bands vary nuisance profile and local marker slot, but are not claimed to form a monotonic cognitive-difficulty scale.

### D4 — Make validation exact and fail loud

`self_check` and `strict_canonical_like` now require a 4×4 integer ARC grid, exactly one red marker, and one exact canonical decoration profile. Wrong scalar types, unknown controls, malformed grids, and singleton impostors are rejected. `seed` and `sample_index` do not accept booleans or coercible strings/floats. This closes the prior validator blind spots without inventing geometric restrictions on decoration placement.

### D5 — Add executable semantic contracts

The generator now includes an independent `rule_mirror`, four branch witnesses, four constant-quadrant rivals, row-half-only and column-half-only rivals, and `lesson_identifiable`. Labels are checked against the mirror before competitor tests. These hooks support framework semantic checks but do not replace the selected Racket authority.

### D6 — Declare the finite output alphabet

`EXPECTED_OUTPUT_CODOMAIN = 4` is derived directly from the four possible marker quadrants. The linter samples all four outputs, so the low output uniqueness ratio is intrinsic rather than a collapse. `workspace/probe_contract.py` also exhausts the codomain.

### D7 — Synchronize the selected authority copy without changing semantics

The canonical `program_solution` was already active and passed rule smoke. The selected base `racket_target.target_code` had different text. Before editing, the authority checker executed both distinct programs and reported parity over all canonical cases. Only `/racket_target/target_code` in the bound task-specific base record was replaced with the existing canonical program. Canonical source and archival `raw_code` were not modified; `checks/authority-sync-manual.json` records exact before/after hashes. Final authority-sync, Racket lint, rule smoke, and defect lint are green.

## Final evidence

- Generator SHA-256: `21ab150fecd7bb6f62ca9914f873a6efb87dfb7698e61711844070b36ae4f519`.
- Final strict battery: 12/12 green in `checks/after-final/`, with required query rotations and the fixed-seed schedule receipt attached.
- Focused task suite: 127 passed, including exact axes, canonical labels, schedule, rivals, retained counterexample, and runnable maintainer probe.
- Random lesson census: 300/300 production lessons and 1,200/1,200 rotations identifiable; 1,200 unique inputs.
- Fixed schedule census: 12/12 lessons and 48/48 rotations identifiable at seed 0 over every declared start residue and all three bands.
- Maintainer probe: 64/64 exact axis combinations and 48/48 finite schedule cases pass; four distinct outputs equal the declared codomain.

Imported historical evidence remains under `evidence/`; it was used only as a lead. Current claims above come from this packet's source-bound checks.
## Current reviewer considerations

Source SHA-256: `21ab150fecd7bb6f62ca9914f873a6efb87dfb7698e61711844070b36ae4f519`.

# Decision ledger — review-c2e33cd2f91f8fab

## D1 — Treat the canonical 4×4 domain as the contract

**Observed state.** The selected corpus contains only 4×4 inputs with one red marker and quadrant boundaries after row/column 1. The baseline advertised an even `grid_n` range through 14, but its implementation did not provide a coherent generalized rule and the linter could not even probe the declaration.

**Decision.** Remove the size axis and make 4×4 exact.

**Rejected alternatives.** Generalizing to larger even grids would require deciding whether the marker selects a half-grid, a fixed 2×2 block, or another geometry. None is established by the selected authority. Keeping the dead axis as a compatibility alias would continue to overstate training support.

**Failure mode / limit.** The repair deliberately cannot generate unseen sizes. That is reported as scope, not hidden as diversity.

## D2 — Publish only exact, observable axes

**Decision.** Keep three controls: `marker_quadrant`, local `marker_slot`, and `decoration_profile`. `observe_overrides` recovers all three directly from pixels, and every Cartesian combination is legal.

**Rejected alternatives.** Free decoration count, free palette size, texture labels, or a generic “bias” axis were removed because they either overlapped, had invalid combinations, or did not correspond to one exact observable property.

**Evidence.** The focused tests and `workspace/probe_contract.py` enumerate `4 × 4 × 4 = 64` combinations and compare requested versus observed values.

## D3 — Match the four canonical decoration profiles rather than broad marginals

**Observed state.** Canonical labeled inputs have decoration signatures `(3 cells, 3 colors)`, `(4,4)`, `(7,4)`, and `(7,6)`. The baseline generated only 3–5 colors and excluded color `0`, so the six-color profile was unreachable.

**Decision.** Use those four exact profiles and sample from `(0,1,3,4,5,7,8,9)`.

**Rejected alternatives.** A broad count range would include unsupported combinations and make `self_check` weaker. Copying the four canonical grids would eliminate useful positional and color variation.

**Failure mode / limit.** Spatial decoration arrangements are varied but not exhaustive. Only profile counts are source-bound.

## D4 — Make one four-answer curriculum period and use three demonstrations

**Observed state.** The old formula `(seed + 2*sample_index) % 4` produced only two quadrants at a fixed seed. A three-demo lesson could therefore omit one entire top/bottom or left/right bit.

**Decision.** Schedule `(seed + sample_index) % 4`, declare period 4, and keep three demonstrations plus one query. Any three of four consecutive branches show both row halves and both column halves.

**Rejected alternatives.** Pure random quadrants can accidentally repeat and provide no period guarantee. Four demonstrations would be redundant for this finite two-bit rule and reduce query efficiency. A handcrafted fixed order without query rotation would leave positional shortcuts untested.

**Evidence.** `counterexamples/two-quadrant-schedule.json`, fixed-period census (12 lessons/48 rotations), random census (300 lessons/1,200 rotations), and the finite probe (48 cases).

## D5 — Hold nuisance axes constant inside each answer block

**Decision.** Marker slot and decoration profile are fixed across each aligned four-answer block, with deterministic block and difficulty offsets.

**Rationale.** If nuisance values co-vary with quadrant, a small model can predict the output branch from clutter complexity or local marker position instead of learning which half contains the red marker.

**Rejected alternatives.** Fully independent random nuisances improve visual diversity but can create accidental correlations in a four-pair lesson. A single global nuisance value would avoid correlation but impoverish the full dataset.

**Failure mode / limit.** Difficulty bands vary nuisance settings; they are not claimed to be a monotonic cognitive-difficulty scale.

## D6 — Validate the exact grammar and reject coercions

**Decision.** Require a rectangular 4×4 integer-color grid, exactly one color-2 marker, and one declared decoration profile. Reject booleans, floats, strings, negative sample indices, unknown axes, and invalid axis values.

**Rejected alternatives.** Permissive coercion makes reproducibility dependent on caller behavior. A minimal validator that checks only the red marker admits examples outside the selected distribution and gives the shared gates false confidence.

**Evidence.** Strict defect lint is green; task tests cover malformed grids and scalar types.

## D7 — Separate generation from rule evidence

**Decision.** Add an independent Python `rule_mirror`, executable rivals, semantic witnesses, and `lesson_identifiable`. The lesson hook verifies labels before checking competitor disagreement.

**Named rivals.** Always choose each fixed quadrant; choose only the row half; choose only the column half.

**Rejected alternatives.** Morphology-only assertions cannot show that a generated lesson disambiguates the rule. Using the same helper for generation and mirroring would make shared bugs self-confirming.

**Failure mode / limit.** Finite rival coverage is evidence against plausible shortcuts, not a proof of unique program induction.

## D8 — Declare the finite output codomain

**Decision.** Set `EXPECTED_OUTPUT_CODOMAIN = 4`.

**Rationale.** Low output uniqueness is intrinsic: there is exactly one output mask per quadrant. Without the declaration, diversity tooling can mistake a correct finite rule for collapse.

**Evidence.** The linter and finite probe both observe exactly four outputs.

## D9 — Synchronize only the selected authority copy after proving parity

**Observed state.** Canonical `program_solution` and the selected base `target_code` were textually different, while the canonical program already passed all examples.

**Decision.** Run the authority parity checker first, then replace only the selected base record’s `target_code` with the existing canonical program. Do not change the canonical ledger or archival `raw_code`.

**Rejected alternatives.** Rewriting the rule would introduce semantic risk. Leaving the stale selected copy would keep authority-sync red. Editing archival history would destroy provenance.

**Evidence.** `checks/authority-sync-manual.json` records old/new hashes and parity; final rule smoke, Racket lint, and authority sync are green.

## D10 — Retain compact future-agent probes

**Decision.** Add `workspace/probe_contract.py` and the old-schedule counterexample. The probe binds its report to generator SHA-256 and exhausts canonical pairs, axes, output codomain, cyclic lessons, query positions, and nuisance-block invariants.

**Rejected alternative.** Relying only on the 12-stage battery makes future diagnosis slower and obscures which finite invariant failed. The probe does not replace Racket checks; it supplies a fast task-local first line.

## D11 — Stop at source-bound completeness

Work stopped after the final source passed all 12 strict battery stages, 127 portable tests, the 64-axis/48-schedule probe, the 300-lesson/1,200-rotation census, the exhaustive period census, and the exposed solve. No unresolved task-local failure remains. Noncanonical sizes, alternate grammars, undeclared rivals, and semantic generalization beyond the selected source remain explicitly out of scope.
