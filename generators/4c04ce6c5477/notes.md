# Working notes: 4c04ce6c5477

## 2026-10-03 review repair

The v3.1 baseline had a stale nine-axis contract, dead helpful textures, contradictory difficulty/global bounds, accepted unknown controls, no `RULE_HASH`, and no executable semantic contract. Version 4.0.0 replaces that surface with exact `grid_h`, `grid_w`, and `n_blobs` controls and constructs every legal cross-product without rejection fallbacks.

The curriculum explicitly refutes four plausible wrong rules: largest area first, left-to-right, top-to-bottom, and numeric color. The selected Racket authority was not changed. See `workspace/reference_probe.py`, `workspace/lesson_probe.py`, and `tests/test_generator.py` for reusable evidence.

Final adversarial review also found and repaired the two-object height-1 runner-up edge: the tallest is now an exact L, so the runner-up is strictly larger by area rather than merely defeating the area rival through a tie-break. The regression replay is seed 0, sample 53 with exact overrides 7×10 and 2 blobs.
## Current reviewer considerations

Source SHA-256: `a21a2f0849003aed495c8263ee7dea4b417a2e018f57ca6478234ec2e71aaf6a`.

# Decisions for `4c04ce6c5477`

## Evidence starting point

No prior return was used as an implementation lead. The associated-note ledger was empty. The immutable selected baseline, canonical examples, selected Racket authority, and retained passing example `b90d4c3d5553` were the only starting references.

## 1. Keep the selected authority unchanged

**Decision.** Pin `RULE_HASH = "cf026680a0b6"` and leave the Racket source and canonical row untouched.

**Reason.** The authority consistently maps each isolated monochrome object to its color and orders those colors by descending bounding-box height. Baseline rule smoke and authority synchronization passed, and an independent Python transcription reproduced all three usable canonical pairs.

**Rejected alternative.** Altering tie behavior or broadening the Racket rule. Canonical inputs and the intended training domain already use distinct heights, so a rule edit would add risk without repairing the actual defect.

## 2. Replace the stale nine-axis surface with three exact axes

**Decision.** Advertise only `grid_h=7..16`, `grid_w=10..18`, and `n_blobs=2..5`.

**Reason.** These are observable properties of the generated input and can be honored exactly for every legal cross-product. The baseline's palette, density, position, and texture controls were either singleton metadata, aliases with no effect, or ordinary-domain entries for negative fixtures.

**Rejected alternative.** Preserve dead axes for API compatibility. Silent controls are worse than a smaller truthful interface: they corrupt provenance and make curriculum requests non-reproducible.

**Failure mode guarded.** The new tests exercise low/canonical/high exact tuples in every band, reject unknown keys and invalid types/ranges, and compare both independent and generator-provided observations.

## 3. Use constructive bands instead of rejection sampling

**Decision.** Partition the grid into object bands separated by a blank column, then construct one object in each band.

**Reason.** This makes isolation, object count, and every width/count override feasible by construction, including 5 objects on the smallest 7×10 canvas. It also avoids rare fallbacks that return a partially built or off-contract grid.

**Rejected alternative.** Randomly place arbitrary blobs until enough happen not to collide. That path needs retries, creates seed-dependent acceptance bias, and makes exact override guarantees difficult to prove.

**Known limitation.** Band separation is a generator convenience and a learnable visual regularity. The semantic witnesses counter the main ordering shortcuts, but future work could add a second constructive packing family with non-monotone band geometry while retaining exact guarantees.

## 4. Vary object count while weighting canonical profiles

**Decision.** Generate 2–5 objects, with strong sampling mass on three objects and 7×11 / 8×12 canvases.

**Reason.** Variable output length prevents a model from treating the task as a fixed three-token palette, while weighted canonical profiles preserve strong support near the original task. The repaired profile-floor gate measured exact-profile support in every band.

**Rejected alternative.** Exactly three objects everywhere. It is canonical-like but unnecessarily narrows the learned algorithm.

## 5. Keep heights distinct and consecutive

**Decision.** Draw a legal starting height and use consecutive distinct heights.

**Reason.** Strict separation makes the intended rank unambiguous and guarantees a scalable area counterexample using the second-tallest object. Consecutive heights also force the learner to compare rather than rely on a large fixed height gap.

**Rejected alternative.** Permit height ties and rely on the authority's secondary left/color ordering. That would mix a separate tie-breaking lesson into a task whose canonical evidence does not establish ties.

## 6. Construct explicit shortcut counterexamples

**Decision.** Every generated input is designed so:

- the tallest object is not leftmost;
- the tallest is bottom-aligned while the second-tallest begins at row 0;
- the second-tallest has strictly greater area than the tallest;
- height-ranked colors are not numerically ascending.

**Reason.** These conditions falsify left-to-right, top-to-bottom, largest-area-first, and numeric-color sorting without relying on aggregate frequency.

**Rejected alternative.** Hope randomization occasionally breaks each correlation. Frequency-only diversity can leave complete lessons ambiguous, particularly at small lesson sizes.

## 7. Make the area witness carry shape diversity

**Decision.** Build the second-tallest object as a connected bbox-exact sparse shape with just enough cells to outrank the tallest by area. In the one-row edge case, make the tallest an L and use a wider runner-up.

**Reason.** The first implementation passed 29/32 tests but produced non-rectangular objects in only 41–53 of 128 band samples because both teaching objects consumed the wide bands. Moving shape variation into the mandatory area witness raised the distribution above the test threshold without weakening any semantic guarantee.

**Rejected alternative.** Lower the diversity threshold. The failing measurement exposed a real curriculum regularity; changing the generator was the correct response.

## 8. Add independent probes and executable semantic hooks

**Decision.** Add:

- `workspace/reference_probe.py` for independent object analysis, canonical fixtures, intended output, rivals, and override observation;
- `tests/test_generator.py` for rule pinning, canonical support, exact overrides, invalid controls, deterministic distribution, semantic hooks, and malformed inputs;
- `workspace/lesson_probe.py` for 100 Racket-backed complete lessons per band using the public production runtime.

**Reason.** Future reviewers can reproduce claims without copying generator internals or trusting prose. The extended probe records source hashes, sampler policy, domain bounds, unique inputs, disagreements, survivors, and replay tuples.

**Limitation.** Named rivals are finite. Passing them is evidence against specific shortcut classes, not universal identification.

## 9. Validator scope

**Decision.** `self_check` accepts the lawful structural manifold: rectangular ARC grid, 7..16 by 10..18, background present, 2..5 monochrome connected objects, unique colors, and unique bbox heights.

**Reason.** It accepts all canonical inputs and generated samples while rejecting malformed, tied-height, mixed-component, and duplicate-color impostors.

**Deliberate non-check.** It does not require every lawful external input to contain the generator's anti-shortcut arrangements. Those arrangements are curriculum guarantees, not properties of the task's full semantic domain.

## 10. Close the two-object area-tie edge case

**Decision.** In the only case where the runner-up can have height one, paint the 2×2 tallest object as an exact three-cell L rather than with the stochastic branch painter.

**Reason.** Final adversarial review found the concrete replay `(seed=0, sample_index=53, grid_h=7, grid_w=10, n_blobs=2)`: the branch could fill all four cells, tying the four-cell runner-up. The area-order rival still disagreed because the objects were oppositely positioned, but the stronger documented guarantee—runner-up area strictly greater than tallest area—was false.

**Test-first evidence.** `checks/final-verification/area_edge_red.log` records `4 > 4` failing before the repair; `area_edge_green.log` records the same regression passing after the exact-L construction. The complete final task suite is 33/33 green.

**Rejected alternative.** We did not weaken the documentation to say only that the area rival disagrees. A constructive strict inequality is cheap and gives future curriculum probes a clearer invariant.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-4292d812db8d55cb:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `a21a2f0849003aed495c8263ee7dea4b417a2e018f57ca6478234ec2e71aaf6a`. At disposition, audited bytes match the current source.

### Current decision

Bounded no-issue:33tests, strict rotations,300uniqueinputs,1440exact-axis cases and3canonical oracle comparisons. Excluded equal-height/touching/multicolor domains explicit. Explicit finite reviewer-reported assessment of these exact audited bytes; no blanket correctness or closure of other findings.

### Assessment or prior finding

## 4c04ce6c5477

**No issue found within the declared domain.** Assigned generator SHA-256: `a21a2f0849003aed495c8263ee7dea4b417a2e018f57ca6478234ec2e71aaf6a`; version `4.0.0`; rule hash `cf026680a0b6`.

The portable task-test stage passed all 33 focused tests (`checks/audit/4c04ce6c5477-task-tests/result.json`), and the strict semantic gate with required query rotations passed (`checks/audit/4c04ce6c5477-semantic/result.json`). I also ran an independent finite probe over 300 generated inputs using seeds `73000..73299`, sample index `i*17`, and cycling easy/medium/hard. All 300 were valid and unique, and all 300 disagreed with each declared plausible shortcut: largest-area-first, left-to-right, top-to-bottom, and numeric-color order.

The same probe exercised every advertised exact axis tuple in every difficulty route: `grid_h=7..16`, `grid_w=10..18`, `n_blobs=2..5`, and difficulty in `{None,easy,medium,hard}`. All 1,440/1,440 combinations were valid and exactly observable; all three canonical pairs matched an independent height-order oracle. Reproducer and report: `checks/audit/4c04ce6c5477-probe/probe.py` and `checks/audit/4c04ce6c5477-probe/audit.json`.

**Domain question, not a reproduced defect:** equal-height ties, touching objects, and multicolor components are intentionally excluded by the declared isolated, monochrome, distinct-height manifold. Their authority behavior remains untrained outside that domain. No files in the audited generator were modified.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
