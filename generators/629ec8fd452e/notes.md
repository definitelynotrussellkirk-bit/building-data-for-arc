# Current notes: `629ec8fd452e`

## Intended rule

On a 0-background grid, split nonzero cells into 4-connected same-colour components. Keep a component exactly when it encloses a 4-connected background region that cannot reach the border of that component's bounding box. Erase solid components and open almost-rings. The canonical Racket authority remains unchanged at rule hash `83b51fc36bb6`; `rule_true` is only the independent Python mirror used by checks.

## Review repair (`3.0.0` -> `3.1.0`)

The prior generator always used a 7-cell 3x3 leaking almost-ring, while true-hole objects had 8, 9, or 14 cells. The wrong conjunction `bbox_interior_missing AND cell_count >= 8` consequently fit all 4 canonical examples and all 600/600 plus 720/720 generated pairs in two retained audits.

Version `3.1.0` reverses that choice. The leaking distractor is now a randomly rotated 9-cell 3x4 frame with one non-corner border gap, matching the 9-cell irregular true-hole survivor. The combined shortcut is declared as `bbox_missing_interior_at_least_8` and is paired with witness `large_open_gap_rebuts_bbox_size_threshold`.

The public call now validates literal integer seed, literal nonnegative integer sample index, difficulty enum, unknown override keys, literal in-range integer axes, and literal `solid|open` role values before `gen_ctx` is constructed.

## Retained distribution decisions

- Grid size: 9..14 by 10..16, with the existing canonical-scale anchor retained.
- Hollow components: 1..2; solid components: 1..2; exactly one leaking false-hole object.
- Every ordinary scene includes five shortcut rebuttals: open gap, large open gap overlapping survivor size, irregular true-hole shape, cross-role colour sharing, and equal kept/erased cell count.
- Shapes are separated by at least one blank row or column; palette and orientations remain randomized.
- Lessons require 3 demonstrations. Five declared rivals are scored for lesson identifiability.

The original rationale for the old 7-cell shape was not recorded; it was likely chosen as the smallest connected open 3x3 frame. It was rejected because it leaked size information. Broader random leaking-frame families were considered but not needed for this bounded repair and would add placement/override failure modes.

## Evidence

Final generator SHA-256: `e6df6a7650d7c55baee9f373aca09d9097bd2430c40e2ab87815ba0ab8b6a2aa`.

- 12/12 after-battery stages green: `checks/after/checks/629ec8fd452e_after_battery_summary.json`.
- 34/34 focused tests pass: `checks/task-tests/result.json`.
- 192/192 sampled scenes trigger every witness and refute every declared rival, with no validator or size-overlap failures: `checks/repair-probe-rerun.json`.
- 300/300 lessons materialized; 0 production ambiguities and 0/1200 required query-rotation ambiguities: `checks/lesson-census.json`.
- Exact 9x12 counterexample, rival output, Racket receipt, and resolution: `counterexamples/review-6260ee24a1c08425-v0001/`.
- Portable regression file: `tests/test_review_regressions.py`.
- Reusable future-agent probe: `workspace/probe_final_support.py`.

The original fixture `tests/test_generator_629ec8fd452e.py` is unchanged from packet baseline SHA-256 `4c208a2af61b220d10298fab9dfc2eea26e9a3a8434b5b0e3cc36d33e2eb4de6`.

## Known limits and open findings

The finite checks cover five declared rivals, not every conceivable program. The sampler still has a bounded template vocabulary, even though colour, placement, orientation, counts, dimensions, and role sharing vary. The random 300-lesson census does not exhaust all seeds or undeclared cyclic starts. No known label or validator defect remains for the selected generator; further shape-family expansion would be a separate design change.
## Current reviewer considerations

Source SHA-256: `e6df6a7650d7c55baee9f373aca09d9097bd2430c40e2ab87815ba0ab8b6a2aa`.

# Decisions for `629ec8fd452e`

## 1. Preserve the authority; repair the curriculum

**Prior choice:** the canonical Racket rule keeps same-colour 4-connected components that enclose a background region disconnected from the border of the component bounding box. The Python mirror already agreed with that rule.

**Decision:** leave the canonical Racket source and rule hash `83b51fc36bb6` unchanged. The defect was in what the generator taught, not in what the authority labelled. The final battery's `rule_smoke`, `racket_lint`, and `authority_sync` stages passed; the selected authority has execution parity. An archival base-solution text remains separately identified by the battery as divergent, but the selected canonical authority is synchronized and no authority edit was needed.

**Rejected alternative:** change the reference to make “bbox interior missing” or a size threshold authoritative. That would encode the observed shortcut rather than the intended topology and would contradict the canonical examples.

## 2. Reverse the 7-cell leaking-ring choice

**Prior choice:** every lesson contained a 3x3 almost-ring with one border cell removed, hence exactly 7 cells. The original rationale was not documented; it appears to have been a compact way to distinguish a true hole from an opening to the outside.

**Problem:** all true-hole objects were at least 8 cells. The conjunction “bbox has a missing interior cell AND size >= 8” therefore matched 4/4 canonical pairs and all 600/600 and 720/720 generated pairs in two retained audits. Merely declaring the existing `bbox_missing_interior` rival did not test this conjunction.

**New choice:** use a 3x4 border frame with one of the two non-corner cells on one long edge removed, then randomly rotate it. The object is connected, has 9 cells, has a missing strict-bbox interior, and leaks to the border. It matches the count of the existing 9-cell irregular true-hole survivor.

**Why this bounded repair:** it changes one shape while preserving grid envelopes, placement logic, colours, object counts, and the Racket relation. It also produces a direct per-scene witness rather than hoping that size ranges overlap somewhere across a corpus.

**Rejected alternatives:**

- Randomize many leaking-frame dimensions. This could broaden the grammar further, but it expands layout failure modes and override interactions without being necessary to refute the known shortcut.
- Use an 8-cell leaking shape. That would overlap the 8-cell rectangular survivor but risk being visually too close to the exact 3x3 frame; the 9-cell 3x4 leak gives a clearer topological contrast and matches the irregular survivor.
- Remove the leaking distractor. That would eliminate the shortcut only by dropping the essential true-hole-vs-open-gap lesson.

Evidence: `checks/repair-probe-rerun.json`, `checks/lesson-census.json`, and `counterexamples/review-6260ee24a1c08425-v0001/`.

## 3. Declare the compositional rival explicitly

**Decision:** add `bbox_missing_interior_at_least_8` to `SEMANTIC_RIVALS` and `CANONICAL_SHORTCUTS`, with witness `large_open_gap_rebuts_bbox_size_threshold`. Every ordinary generated scene must refute it.

**Reason:** the canonical pairs themselves do not distinguish this rival; all 4/4 fit it. A curriculum gate can only reject a surviving shortcut that it knows to score. The new declaration makes the failure replayable in task tests, the semantic gate, the support probe, and lesson census.

**Limitation:** this is a finite named hypothesis family. It does not prove that no other conjunction or arbitrary program fits the data.

## 4. Enforce the public call contract before `gen_ctx`

**Prior behavior:** integer overrides and `sample_index` accepted bools, floats, or numeric strings in several paths; the top-level call also had no explicit difficulty/seed boundary.

**Decision:** validate before constructing `gen_ctx`:

- `type(seed) is int`;
- `type(sample_index) is int` and `sample_index >= 0`;
- difficulty is one of `None`, `easy`, `medium`, or `hard`;
- unknown override keys are rejected;
- each integer axis is a literal integer in its declared range;
- `shared_reject_role` is the literal string `solid` or `open`.

**Reason:** bool is a Python integer subclass, and coercible scalars can silently select undocumented schedule or override behavior. The baseline defect linter reproduced ten such cases. The final linter and focused tests reject them.

**Rejected alternative:** normalize inputs with `int()` or lowercase strings. That would make malformed upstream jobs appear valid and would keep the same ambiguity at the boundary.

## 5. Preserve inherited distribution controls

The existing 9..14 by 10..16 grid envelope, 1..2 hollow objects, 1..2 solid objects, deterministic canonical-scale anchor, random palette, shared reject role, blank-gap placement, and rotations were retained. Their original full rationale is partly unknown, but the override, grammar, profile, diversity, and placement checks all passed after the bounded change. Changing these independent dimensions would obscure which repair addressed the reproduced shortcut.

One leaking object remains mandatory because it is the decisive negative example for topological enclosure. The generator also retains a non-rectangular true-hole object, cross-role colour sharing, and equal cell counts across kept/erased roles so rectangle, colour, and count-only rivals are contradicted.

## 6. Keep the frozen fixture immutable; add portable regressions

A first red-cycle draft appended tests to the existing fixture, but the packet contract marks that fixture immutable. It was restored byte-for-byte to baseline SHA-256 `4c208a2af61b220d10298fab9dfc2eea26e9a3a8434b5b0e3cc36d33e2eb4de6` before final verification. The regressions moved to new `tests/test_review_regressions.py`, which uses public `reviewer_support.find_root` and `load_selected_generator` APIs and is portable to staged runtimes.

The final suite has 34 passing cases. It covers strict seed/index/override/enum boundaries, generated per-scene size overlap, declaration and refutation of the composite rival, and the retained 9x12 counterexample.

## 7. Retain a source-bound authoring probe

`workspace/probe_final_support.py` is a reusable future-agent tool. It binds to the selected generator SHA, reads canonical pairs through public APIs, samples all difficulty bands, reports validator failures, witness frequency, rival agreement, component-size support, and scalar rejection, and exits nonzero if any required condition fails.

At 64 draws per band it sampled 192 scenes: no validator errors, no size-overlap failures, no rival agreements, all five witnesses present 192/192, and all five rivals refuted 192/192. The observed role sizes were hollow `{8,9,14}`, open-like `{9}`, and solid `{4,9}`.

## 8. Use three demonstrations and test query rotation

The generator declares `EXAMPLES_NEEDED = 3`; production lessons therefore contain three demonstrations and one query. The larger census materialized 300 lessons (100 per band), 1,200 unique labelled pairs, and tested every one of the four positions as query under rotation policy `require`. It found zero production ambiguities and zero rotated-query ambiguities against all five declared rivals.

This supports both the ordinary ordered lesson and arbitrary placement of the labelled query within the four sampled pairs. It does not exhaust all seeds, all possible cyclic starts, or undeclared rivals.

## 9. Keep audit targets findings-only

Per the assignment, `generic_dense_select_gen1` and `a06827026857` were audited but not edited. The first has an absolute `size >= 9` shortcut over 450/450 sampled pairs; the second accepts invalid top-level seed/index/difficulty values despite strict override-axis checks. These are documented in `AUDIT.md`; they are not failures of the repaired assigned generator.

## 10. Stopping decision

Stop after the bounded root causes are repaired, the exact counterexample is Racket-labelled and regression-tested, 34/34 focused tests pass in both the working packet and a fresh exact-patch replay, the 12-stage battery is green, the 192-scene support probe is clean, the 300-lesson/1,200-rotation census has no declared-rival ambiguity, and the post-repair visible solve is complete on the same generator bytes. Further shape-family expansion would be a new design task rather than evidence-driven completion of this repair.

## Native parametric admission candidate (`2026-10-24`)

The accepted production generator and canonical Racket authority remain byte-for-byte unchanged. A task-local native family now lives in `workspace/parametric/`:

- `output_scope=all_holes` is the exact canonical program (`83b51fc36bb636684688017b2a9ca7cc81a2f807a5b6d1c8bb9bf31be7323d68`).
- `output_scope=largest_hole_color_relay` first identifies true-hole source components and sums their enclosed regions, selects the row-major first color with maximum total enclosed area, then keeps every disconnected component of that color, including non-hole relays.

This alternative was chosen because B genuinely depends on A's input-derived topology/area result. The protected-Racket witness in `checks/629ec8fd452e/causal/witness.json` replaces A with a largest-foreground shortcut; the intermediate and final grid change. The family supports 2..6 demonstrations and exactly four stable-prefix queries, with a 30x30 boundary query and one-query public projections whose IDs hash only visible bytes.

The first finite teaching audit exposed two real holes: `rectangular_frame_only` survived the canonical lesson and `largest_single_hole_color_broadcast` survived the relay lesson. The two-demo curriculum was repaired constructively by adding a tabbed true-hole source and a double-chamber source whose total enclosed area differs from its largest individual cavity. No extra demonstration was required.

Retained evidence:

- 67/67 staged task tests: `checks/629ec8fd452e-tests/result.json`.
- 384 authoring episodes across 64 seeds, both settings, and demo counts 2/3/6; zero finite-rival failures: `workspace/parametric/evidence/current/summary.json` and `teaching-audit.json`.
- Native qualification for both settings at seeds 0 and 17, 40 protected-Racket evaluations: `checks/629ec8fd452e/qualification/qualification.json` and `execution.json`.
- Replayed A/intermediate/B counterfactual: `checks/629ec8fd452e/causal/witness.json` and `replay.json`.
- Public-export reports are normalized to repository-relative paths by the reusable `verify.py --normalize-public-check` mode before inventory or return.

Reviewer status is **native ready, owner acceptance pending**. This does not claim canonical approval of the alternative setting, production integration, or training admission.
