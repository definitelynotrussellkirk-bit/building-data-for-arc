# Working notes: b7ff231aab1a

## Current rule and authority

The selected canonical Racket authority is unchanged and pinned as `RULE_HASH = "5c4099040cb4"`. Count all maroon (9) cells to obtain one-indexed rank K; sort the three blue (1) components by area (bbox top-left only as a deterministic tie-break), crop rank K, upscale 2×, and recolor occupied cells cyan (8).

## Review repair (version 2.0.0)

The imported 1.2.1 generator exposed nominal palette/texture controls that did not match its emitted pixels, swallowed unknown controls, failed exact overrides and canonical-profile checks, represented marker counts with isolated cells unlike the canonical marker bars, and had no executable semantic contract. More importantly, all six canonical pairs also fit the simpler rule “take the K-th blue component in reading order.”

The replacement keeps the authority fixed but narrows the generator to a source-linked exact contract:

- canonical colors only: background 0, components 1, marker 9, output 8;
- grid height 11..12 and width 15..17;
- exactly three distinct-area connected polyominoes, with ten observable size profiles;
- marker count 1..3 painted as one contiguous horizontal bar;
- the two complete derangements of size rank across three reading-order slots;
- unknown or invalid overrides reject loudly, and every advertised override is recoverable by `observe_overrides`;
- three-demo lessons cycle marker counts 1, 2, 3 and execute a named-rival contract.

This reverses the prior choices of nominal palette/texture modes, isolated markers, and spatial order aligned with size rank. Evidence for the reversal is the failed before battery (`checks/before/`), the Racket-bound shortcut witness (`checks/generator-shortcuts/`), and the all-green final battery (`checks/after-final/`). No prior return was used as a lead; retained associated notes were empty.

## Counterexample and reusable probe

`counterexamples/reading_order_rank.json` is a stable generated input where the intended area-ranked rule and the canonical-compatible reading-order rival disagree. `workspace/reference_probe.py` independently extracts both predictions without importing the production rule mirror. The canonical Racket application is retained at `checks/generator-shortcuts/racket.json`.

## Known limits and open risk

The lesson evidence refutes the four declared rivals over 300 source-bound lessons and all 1,200 query rotations; it is not a proof against every possible hypothesis. Generated spatial orders are intentionally limited to the two complete derangements, because these are the only three-item permutations that refute reading-order selection for every K. Shape vocabulary is random connected polyominoes within a 3×5 envelope, not every connected shape. Difficulty changes nonsemantic schedule offsets rather than rule complexity.
## Current reviewer considerations

Source SHA-256: `7d9d14a570624557457f57a698320104c929f87eeaa66a0cbe486e22ec26feeb`.

# Design and review decisions — b7ff231aab1a

## Evidence boundary and prior work

I used the selected 1.2.1 source, its empty current notes, all six canonical pairs, public check outputs, and the canonical Racket authority after completing the required blind solve. `evidence/associated_notes.jsonl` contained no substantive prior-return lead, so no earlier return was treated as evidence for the current source.

## 1. Keep the canonical authority unchanged

**Choice.** Pin `RULE_HASH = "5c4099040cb4"` and change only the generator/tests/workspace.

**Rationale.** The canonical rule is internally coherent and passed rule smoke, Racket lint, and selected execution-parity checks before repair. The defects were in generation and teaching support, not label authority.

**Alternatives rejected.** Rewriting the rule to match baseline isolated-marker or reading-order behavior would have changed the task rather than repaired the generator.

**Probe and failure mode.** All six canonical pairs are checked in task tests; the final battery's rule-smoke and authority-sync stages are green. A future authority change must update the pinned hash and repeat these checks.

## 2. Fix semantic colors to canonical roles

**Choice.** Inputs use exactly 0 background, 1 components, and 9 markers; output uses 8.

**Prior choice reversed.** The baseline advertised multiple “palette” modes while its generation/self-check logic was effectively hard-coded. That made controls nominal and invited role ambiguity.

**Alternatives rejected.** Color permutations were not justified because the canonical rule explicitly selects colors 1 and 9 and emits 8. A palette axis would require a different authority or a proven role-equivalence contract.

**Limit.** This improves source fidelity rather than color generalization.

## 3. Use the canonical dimension envelope

**Choice.** `grid_h ∈ {11,12}` and `grid_w ∈ {15,16,17}`.

**Rationale.** These values cover the canonical profiles and provide enough separated area for three 3×5 component envelopes and a marker bar. The final profile-floor check hit exact canonical profiles in every band (49 exact hits among 60 draws).

**Alternatives rejected.** The broader legacy dimensions were not exact, often ignored overrides, and contributed no semantic coverage. Smaller grids make the largest size profiles or separation constraints brittle.

**Limit.** The generator does not test arbitrary board scale; that is explicitly outside the declared domain.

## 4. Use ten distinct-area size profiles

**Choice.** Retain ten observable triples: `(2,3,4)`, `(2,3,5)`, `(2,4,5)`, `(3,4,5)`, `(2,6,8)`, `(3,7,9)`, `(4,8,11)`, `(5,10,13)`, `(6,12,14)`, `(7,13,15)`.

**Rationale.** The small profiles preserve canonical-like output sizes; larger profiles force actual component counting and broaden crop/output geometry. Strictly distinct sizes remove tie ambiguity while preserving the rule's deterministic bbox tie-break.

**Probe.** The override stage accepted all 14,400 attempts across 160 cases and three bands; `observe_overrides` recovered every requested profile.

**Failure modes considered.** A singleton component would make shape recognition trivial; profiles therefore start at area 2. Sizes above 15 would not fit the fixed 3×5 shape envelope.

## 5. Generate random connected polyominoes in a 3×5 envelope

**Choice.** Grow keyed random 4-connected shapes, reflect them randomly, and use a deterministic connected fallback.

**Rationale.** Shape diversity prevents the task from reducing to memorized canonical silhouettes while area remains the intended selector. The envelope gives predictable placement capacity for every supported size.

**Alternatives rejected.** Fixed rectangles or a tiny hand-written shape list would make output dimensions/shape a stronger shortcut. Unbounded random walks made constructive guarantees harder.

**Limit.** This is broad but not exhaustive over all connected polyominoes.

## 6. Use both complete rank derangements

**Choice.** Reading-order area ranks are either `[2,3,1]` or `[3,1,2]`.

**Rationale.** These are the only complete derangements of three ranks. Therefore reading-order selection fails for K=1,2,3 in every generated sample, rather than only somewhere in a lesson.

**Prior choice reversed.** Canonical examples and the baseline aligned reading order with area order, allowing a rival to fit all demonstrations.

**Alternatives considered.** Including partially aligned permutations would increase permutation support but permit reading order to answer some generated queries correctly. The complete derangements provide the strongest local counterexample while both layouts still vary.

**Limit.** A solver can learn a two-permutation support table; the contract claims area ranking, not exhaustive permutation coverage.

## 7. Represent K as one contiguous horizontal marker bar

**Choice.** Paint exactly K adjacent 9-cells in a row, with K in 1..3.

**Rationale.** Canonical inputs encode K as a contiguous horizontal bar. The baseline's isolated-marker grammar was a source mismatch and allowed “number of marker components” to stand in for “number of marker cells.”

**Alternatives rejected.** Scattered or vertical markers would be reasonable only as an explicitly broadened grammar with counterexamples and source justification.

## 8. Use three-demo lessons with K cycling 1,2,3

**Choice.** `EXAMPLES_NEEDED = 3`; ordinary schedules set marker count by `sample_index % 3`. Grid dimensions, size profiles, and rank layouts advance on different periods and seed/difficulty offsets.

**Rationale.** Three examples expose every possible K and refute constant-rank rivals inside every cyclic three-demo start. Different axis periods avoid a single pair of controls moving in lockstep.

**Difficulty decision.** Difficulty changes nonsemantic schedule offsets only. An earlier revision left bands byte-identical; defect lint caught this. Offsets now make distributions distinct without inventing a different rule by band.

**Probe.** Task tests enumerate every cyclic start; the required-rotation semantic gate and 300-lesson census both pass.

**Limit.** Difficulty is distributional, not a calibrated reasoning-complexity score.

## 9. Advertise only exact, recoverable controls

**Choice.** Public axes are `grid_h`, `grid_w`, `marker_count`, `size_profile`, and `rank_layout`; invalid values and unknown keys fail loudly; no incompatible combinations are declared.

**Prior choice reversed.** Legacy texture/palette controls were dead, degenerate, or could deliberately violate self-check. Grid dimensions were often ignored.

**Rationale.** A smaller truthful contract is preferable to a broad fictional one. All 720 joint combinations per band are constructive in task tests, and the public override checker probed the complete advertised value set.

## 10. Declare and execute the semantic rival contract

**Choice.** Register reading-order rank and always-smallest/middle/largest rivals; mark reading-order rank as canonical-compatible; provide executable witnesses and `lesson_identifiable`.

**Rationale.** Correct individual labels do not guarantee a teachable lesson. The strongest canonical shortcut needed to be explicit and mechanically refuted.

**Alternatives rejected.** Treating semantic checking as advisory left the central defect unmeasured. Adding many contrived rivals would make reports look broader without improving plausibility.

**Limit.** Passing a finite rival set is not proof of unique induction. This limitation is recorded in the census and review.

## 11. Retain a stable counterexample and reusable independent probe

**Choice.** Add `counterexamples/reading_order_rank.json` and `workspace/reference_probe.py`.

**Rationale.** Future reviewers can recompute intended and rival predictions directly from pixels without importing the production mirror, then independently bind the result to Racket with `arcpuzzles apply`.

**Probe.** A task test first failed because the tool did not exist, then passed after implementation; the final task suite verifies its predictions against both production functions on the stable witness.
