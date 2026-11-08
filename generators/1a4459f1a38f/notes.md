# Working notes: 1a4459f1a38f

## 2026-10-02 review

### Measured baseline

The required before battery passed 11 stages but failed `semantic_gate`: only `7/12` sampled lessons were identifiable. The retained gate report showed three printed examples and the JSON/replay analysis found five failures in total. The surviving query-changing rivals were `modal_color_all_cells` in three lessons and `largest_bbox_area` in two. Evidence: `checks/before/checks/1a4459f1a38f_before_semantic_gate.log` and `.json`.

A separate source inspection found an undeclared shortcut: every component had an 8-neighbor moat, so same-color 4-connected and 8-connected object extraction were observationally identical. The task summary explicitly says 4-connected, but the distribution supplied no counterexample.

### Repair

- Added explicit 4- and 8-connectivity mirrors and a named `largest_8_connected` rival.
- Allowed only same-color diagonal target/distractor contact; orthogonal contact and different-color diagonal contact remain rejected.
- Made both repeated-color and irregular slots realize a 4-vs-8 disagreement.
- Strengthened the irregular slot so it simultaneously refutes bbox-area, modal-color, frame-only, and 8-connectivity shortcuts. This duplicates decisive evidence across the four-slot cycle and protects non-aligned three-demo windows.
- Restricted `SEMANTIC_WITNESSES` to four witnesses with declared, verified rival disagreements. Canonical size, shape, and reading-order coverage remains in focused tests rather than being reported as weak semantic evidence.
- Added `CURRICULUM_SCHEDULE` metadata and replay tests for the exact 12 semantic-gate lessons.
- After the first repair, the complete battery found canonical-profile support had fallen from `24/60` to `13/60`: the repeated-color irregular anchor necessarily uses two foreground colors. A separate even-episode bbox-decoy anchor now supplies `10x10` scenes with three distinct foreground colors. The targeted gate reports `19/60` exact/envelope support.

### Verification and retained failures

The change was developed through three red/green cycles retained under `checks/tdd_red*.log` and `checks/tdd_green*.log`. The focused suite is `15 passed`. The reusable `workspace/review_census.py` probe checked 768 grids and 696 contiguous lesson windows with zero lesson failures; all four named witness/rival pairs occurred in every difficulty band. The official targeted profile and semantic gates pass. The intermediate profile failure (`13/60` support) is intentionally retained as a direct replay under `checks/profile_floor_regression_before_fix.log` and `.json`, plus the focused red test in `checks/tdd_red3.log`; the final battery is recorded separately in the top-level review evidence.

### Limitations

The named rival set is intentionally finite. It now covers 8-connectivity, bbox area, global modal color, first/last reading order, and hollow-frame shortcuts, but it cannot prove uniqueness against every possible program. Same-color diagonal contact is deliberately concentrated in two of four slots to make connectivity observable; this is stronger than the public examples and should be monitored for overlearning. Explicit axis overrides use the general branch and therefore do not guarantee the four-slot pedagogical schedule.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `bcd41e19852afc4f643abba9e4353f9404106e6143126a98295b52009481e59d`.

# Decisions: 1a4459f1a38f

## 1. Make connectivity observable

**Choice.** Permit a distractor with the target color to touch the target diagonally while remaining orthogonally disconnected. Add an explicit 8-connected extractor and `largest_8_connected` rival.

**Original rationale.** The imported implementation enforced an 8-neighbor moat. That kept objects visually clean but erased the semantic distinction between the stated 4-connectivity rule and an 8-connectivity shortcut.

**Alternatives.** Keep the moat and merely document 4-connectivity; use diagonal contact between different colors; add only a synthetic unit fixture without changing ordinary generation.

**Probe.** `test_repeated_witness_slots_distinguish_four_from_eight_connectivity` and the `four_connected_not_eight_connected` gate witness. The official semantic gate verifies 60/60 sampled rival claims.

**Failure modes and limits.** Too much diagonal contact could become a superficial cue. Different-color contact would not test same-color component merging. The selected schedule confines the witness to two slots and preserves ordinary moat separation elsewhere.

## 2. Protect every sliding lesson, not only aligned cycles

**Choice.** Keep the four-slot schedule but make the irregular slot repeat the bbox-area and modal-color counterexamples in addition to its frame/shape role.

**Original rationale.** The old test examined starts `0,4,8,12`. The real gate constructs lessons at starts such as `11,22,33`; five of those lessons allowed a query-changing rival.

**Alternatives.** Increase the lesson budget; lengthen the schedule; randomize branch weights; special-case only the 12 pinned gate seeds.

**Probe.** Exact replay of all 12 gate lessons plus all contiguous windows in `workspace/review_census.py`.

**Failure modes and limits.** Redundant counterexamples reduce some independent morphology variation. They were preferred over seed-specific patches because the guarantee now holds across 696 broad-census windows, not only the pinned cases.

## 3. Use a deterministic multi-rival irregular slot

**Choice.** Use a nine-cell, non-frame 3x4 target and a seven-cell 4x4 bbox decoy; repeat the target color on a diagonally touching distractor.

**Original rationale.** An unconstrained irregular target did not always refute bbox area or modal color. The selected construction makes cell count, bbox area, frame status, color aggregation, and connectivity disagree in one legible scene.

**Alternatives.** Search randomly until all witnesses happen to fire; dedicate one slot per rival; use larger grids with more components.

**Probe.** Generator assertions, focused witness tests, semantic rival claims, and the distribution census.

**Failure modes and limits.** The shape grammar is deliberately finite. The slot is pedagogically dense and may be visually harder than canonical scenes, but it remains within the declared 2–4 component grammar and passes all structural gates.

## 4. Separate evidence contracts from profile descriptors

**Choice.** Remove five weak entries from `SEMANTIC_WITNESSES` and retain only witnesses linked to named rivals. Expose `CURRICULUM_SCHEDULE` and keep canonical-size, position, and non-square checks in focused tests.

**Original rationale.** The after-phase gate correctly warned that a feature-presence predicate does not prove any competing rule answers differently.

**Alternatives.** Invent artificial rivals for every descriptive feature; ignore the warnings; remove the descriptive coverage entirely.

**Probe.** `test_semantic_witnesses_are_rival_backed_and_schedule_profiles_are_explicit`; final semantic gate reports no weak witnesses.

**Failure modes and limits.** The smaller witness list is not a smaller curriculum. It is a more honest machine-readable contract; descriptive properties remain tested but no longer inflate semantic evidence counts.

## 5. Restore canonical profile support without weakening repeated-color evidence

**Choice.** Add a 10x10, three-foreground-color anchor to even bbox-decoy episodes. Keep irregular/repeated-color slots at two foreground colors because they must repeat the target color across three components.

**Original rationale.** The first semantic repair lowered canonical-profile support from the imported `24/60` to `13/60`, below the battery's 25% envelope threshold.

**Alternatives.** Remove repeated colors from the irregular slot; use four irregular components so three foreground colors remain; declare a profile opt-out; make every draw canonical-scale.

**Probe.** Exact pinned-seed regression test and the official profile floor. Final result is `19/60` with support in every band.

**Failure modes and limits.** The anchor slightly increases 10x10 mass in bbox-decoy episodes. It avoids a noisier four-component layout and preserves both the semantic witness and meaningful noncanonical scale variation.

## 6. Leave Racket authority unchanged

**Choice.** Change only the generator, tests, notes, summary, and workspace probe.

**Original rationale.** Canonical execution, rule smoke, and authority sync were already green. The defect was distributional identifiability, not rule behavior.

**Alternatives.** Rewrite the Racket rule for explicit tie handling or connectivity; modify canonical examples.

**Probe.** Final `rule_smoke`, `racket_lint`, and `authority_sync` stages all pass with the same authority-set hash as the baseline.

**Failure modes and limits.** The generator still forbids ties rather than defining a tie policy. That matches the current task contract and canonical data.

## 7. Add a reusable census tool

**Choice.** Build `workspace/review_census.py` with a focused test.

**Original rationale.** Future reviewers need a cheap way to distinguish balanced branch coverage from actual rival-answer disagreement and to test non-aligned lesson windows.

**Alternatives.** Rely only on the full battery; keep an ad hoc notebook; add more one-off pytest cases.

**Probe.** `workspace/test_review_census.py` passes; the 768-grid report is retained in `checks/review_census_after.json`.

**Failure modes and limits.** It uses internal Python candidate mirrors. Its nonzero exit is useful for local iteration but does not establish Racket parity; the official battery remains authoritative.
