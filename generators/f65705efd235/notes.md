# Working notes: f65705efd235

## Review 2026-10-02

The previous version excluded a real canonical subcase by requiring both rectangle spans to be at least three cells. Two of five canonical inputs contain a two-cell-wide rectangle, while a retained 600-draw baseline probe produced none. It also declared mostly ignored axes, could silently place fewer rectangles than requested, lacked a structural `self_check`, did not pin the Racket rule hash, and had no executable semantic contract.

Version 3.0.0 narrows the override surface to three exact observable controls, guarantees exact rectangle count, restores thin canonical rectangles, and schedules explicit counterexamples to corners-only, solid-fill, fixed-two-colors, reverse-layering, and ignore-thin shortcuts. A protected interior cell keeps the outline-versus-fill distinction visible even in crowded scenes.

The selected canonical Racket authority was not changed. `workspace/probe_generator.py` is the retained high-volume regression tool.
## Current reviewer considerations

Source SHA-256: `df598a4c9f22f38e6fec481d948022bf5f82bb8a32b8f6c31c1b6eb9500b2fb4`.

# Design and distribution decisions for `f65705efd235`

## 1. Preserve the Racket authority

**Observed baseline:** rule smoke, grammar, Racket lint, authority synchronization, and execution parity were healthy before generator changes. The canonical outputs were reproduced by the selected rule.

**Decision:** do not modify the Racket authority. Add `RULE_HASH = "635fcfe4fd6f"` and a small Python mirror for tests and semantic probes.

**Rejected alternative:** changing the rule merely because the generator battery failed. The failures were generator contracts and coverage, not transformation semantics.

**Probe/evidence:** `checks/before/checks/f65705efd235_before_rule_smoke.json`; `checks/after/checks/f65705efd235_after_authority_sync.json`.

**Limitation:** the Python mirror is secondary executable evidence, not a replacement authority.

## 2. Replace the broad pretend override surface with three exact axes

**Observed baseline:** declared axes were mostly ignored. The immutable override audit reported more than 14,000 requested-versus-observed mismatches, omitted provenance, and acceptance of an unknown key.

**Decision:** expose only `grid_h`, `grid_w`, and `n_rects`. Validate types and ranges before any draw; reject unknown names; route defaults and overrides through keyed draws; provide `observe_overrides` so the contract is independently measurable.

**Ranges:** dimensions are `7..24`; rectangle count is `2..6`. These retain the prior scale envelope while keeping the minimum dimensions large enough for the teaching pair and exact six-object placement.

**Rejected alternatives:**

- Keep axes for palette, texture, orientation, overlap, or color order. Those were not honest exact controls and would multiply incompatible combinations.
- Make all internal random choices caller-controlled. That exposes implementation details rather than stable, observable behavior.
- Silently clamp invalid values. That converts caller mistakes into mislabeled data.

**Probe/evidence:** `checks/before/checks/f65705efd235_before_override_results.json`; `checks/after/checks/f65705efd235_after_override_results.json`; boundary-cross tests in `repo/generators/f65705efd235/tests/test_generator_f65705efd235.py`.

**Limitation:** callers needing exact color identities or individual rectangle coordinates cannot request them through the public API.

## 3. Restore the two-cell-thick canonical subcase

**Observed baseline:** the old inequalities required both corner-row and corner-column differences to be at least two, forbidding width-two and height-two rectangles. Two canonical inputs contain such a rectangle; 600 old draws contained none.

**Decision:** every draw includes either a two-cell-wide or a two-cell-high rectangle. A 2×2 rectangle remains forbidden because its border is exactly the four given corners and teaches no expansion.

**Rejected alternatives:**

- Make thin rectangles merely possible. A rare random branch could still leave short lessons without evidence.
- Copy only canonical dimensions while retaining the old shape grammar. That would improve the coarse profile score without fixing the semantic hole.
- Permit 2×2 quads. They are lawful under a literal border reading but are uninformative for learning the transformation and could support identity-like shortcuts.

**Probe/evidence:** `checks/logs/baseline-thin-subcase-probe.log`; `checks/f65705efd235-probe-final.json`.

**Limitation:** guaranteeing a thin rectangle in every draw over-represents it relative to the five canonical inputs. This is deliberate curriculum coverage rather than a claim of natural frequency.

## 4. Use a deterministic four-position curriculum

**Observed baseline:** random independent draws did not guarantee that a three-example lesson exposed object-count, overlap-order, outline-vs-fill, or thin-rectangle distinctions.

**Decision:** use four deterministic schedule positions per difficulty. Counts are arranged so every three-consecutive-example window includes more than two rectangles, while half of the positions still use exactly two. Each position retains random geometry and colors under the seed.

**Difficulty profiles:**

- `easy`: compact canonical-scale dimensions with counts 2, 3, 2, 4;
- `medium`: mixed 9–16 cell dimensions with counts 2, 3, 2, 4;
- `hard`: one canonical-scale anchor plus larger 14–24 cell scenes and counts up to 6.

**Rejected alternatives:**

- Pure IID count sampling. It can produce three two-object examples and leave the fixed-two shortcut viable.
- Always use many rectangles. That removes simple examples and needlessly increases visual clutter.
- Encode the schedule in the seed rather than `sample_index`. `sample_index` is the natural curriculum position and is directly checked by the semantic gate.

**Probe/evidence:** schedule-window tests in `repo/generators/f65705efd235/tests/test_generator_f65705efd235.py`; `checks/after/checks/f65705efd235_after_semantic_gate.json`.

**Limitation:** the four-position cadence is detectable. It is a lesson-design mechanism, not intended as an unpredictable natural-data sampler.

## 5. Guarantee a teaching pair, then add free rectangles

**Decision:** start each scene with a transformed pair consisting of one canonical thin rectangle and one thick rectangle whose borders cross. Random row/column reflections prevent a fixed-location shortcut. Additional rectangles are sampled afterward.

This single pair guarantees three high-value relations: border expansion beyond corners, a hollow interior, and an overlap at which layer order can matter.

**Rejected alternatives:**

- Generate all rectangles independently and hope useful relations occur. Early high-volume probing showed even a 99.97% frequency was insufficient: two seeds allowed later borders to erase the only hollow-cell distinction.
- Hand-author one fixed template without reflections or random additions. That would make coordinates and sizes too predictable.
- Require all rectangles to be disjoint. That makes ascending color order unobservable.

**Probe/evidence:** the two failing rare seeds are retained in `checks/logs/tdd-red-hollow-witness.log`; the repaired 6,000-draw result is `checks/f65705efd235-probe-final.json`.

**Limitation:** all scenes contain overlap, so non-overlap-only scenes are omitted. For this task, overlap is needed to identify the authority’s overwrite order.

## 6. Protect one hollow interior cell

**Observed counterexample:** in two rare crowded scenes, later rectangles crossed every interior cell needed to distinguish outline from solid fill.

**Decision:** choose a background cell strictly inside the thick teaching rectangle and reject every later rectangle whose border would cover it. The authority therefore leaves that cell zero while a solid-fill rival colors it.

**Rejected alternatives:**

- Accept a probabilistic floor such as 99%. With three-example lessons, even rare ambiguous draws can create bad training items.
- Post-filter entire outputs after generation. That can waste unbounded retries and hides why placement fails.
- Reserve the whole thick interior. That over-constrains later geometry; one protected witness cell is sufficient.

**Probe/evidence:** `checks/logs/tdd-red-hollow-witness.log`; `checks/logs/tdd-green-focused-tests-final.log`; `checks/f65705efd235-probe-final.json`.

**Limitation:** the protected cell is an internal curriculum invariant and is not exposed as an override.

## 7. Guarantee exact object count with an exhaustive fallback

**Observed baseline risk:** placement stopped after a finite number of random attempts and could return fewer rectangles than requested.

**Decision:** use random candidate placement first for variety. If it exhausts 5,000 attempts, enumerate all row-pair/column-pair rectangles from a deterministic offset and choose the first lawful candidate. Raise a clear exception only if no exact solution exists.

**Rejected alternatives:**

- Increase the retry count and continue silently. That makes under-delivery rarer but leaves the contract false.
- Backtracking over the entire scene. It adds complexity not justified by the small 7–24 grids and 2–6 counts.
- Report the requested count in metadata even when fewer were placed. That would create mislabeled training data.

**Probe/evidence:** exact boundary-cross tests and the 6,000-draw rectangle-count histogram in `checks/f65705efd235-probe-final.json`.

**Limitation:** the fallback is exhaustive over candidate rectangles, not globally backtracking. The selected ranges were stress-tested, but a future expansion to denser object counts may require backtracking.

## 8. Use distinct random nonzero colors and ascending paint order

**Decision:** sample distinct colors from `1..9` and paint their full borders in ascending numeric order on a fresh zero canvas. Larger colors therefore win at shared output cells.

**Rejected alternatives:**

- Preserve sampled order. That would disagree with canonical overlap behavior.
- Avoid overlaps. That would make the order unidentifiable.
- Use repeated colors for separate rectangles. The canonical rule groups cells by color, so repeated colors would merge objects and violate the input grammar.

**Probe/evidence:** all nine colors appear in the retained census; reverse-order behavior is refuted in 6,000/6,000 draws (`checks/f65705efd235-probe-final.json`).

**Limitation:** the color histogram is approximately balanced, not forced exactly equal in every finite sample.

## 9. Add structural self-checking rather than output-only validation

**Decision:** `_analysis` reconstructs each color’s row/column sets and rectangle corners. `self_check` verifies grid shape, ARC colors, dimension/count ranges, exact four-corner structure, non-colliding corners, and optional override observations. `strict_canonical_like` provides the narrower semantic-gate profile.

**Rejected alternatives:**

- Compare only `rule_mirror(input)` to a generated output. A malformed input can still have a deterministic output.
- Validate only cell counts. Four cells need not form a Cartesian-product corner set.
- Put assertions solely inside `generate`. External callers and mutation probes could not reuse them.

**Probe/evidence:** mutation fixtures and malformed-input tests in `repo/generators/f65705efd235/tests/test_generator_f65705efd235.py`; after `selfcheck` and `defect_lint` receipts under `checks/after/checks/`.

**Limitation:** `self_check` validates this generator’s intended domain; it does not attempt to accept every conceivable input on which the Racket program happens to return a value.

## 10. Make semantic alternatives executable

**Decision:** define five rival rules and pair each with a witness:

- keep only corners ↔ an outline adds non-corner cells;
- fill rectangles solid ↔ a strict interior remains background;
- process only two colors ↔ more than two rectangles;
- reverse paint order ↔ overlapping borders;
- ignore two-cell-thick rectangles ↔ a lawful thin rectangle.

`lesson_identifiable` rejects any three-example lesson on which a registered rival still matches the authority.

**Rejected alternatives:**

- Narrative claims in `SUMMARY.md` only. They cannot prevent regression.
- Declare every imaginable shortcut. The contract should contain small, executable, plausible competitors, not an unbounded list.
- Label all rivals as canonical ambiguities. Only fixed-two and reverse-order actually fit all five canonical pairs, so only those are declared in `CANONICAL_SHORTCUTS`.

**Probe/evidence:** `checks/after/checks/f65705efd235_after_semantic_gate.json`; `checks/f65705efd235-probe-final.json`.

**Limitation:** passing these rivals does not prove no other shortcut exists. It makes the major observed and plausible alternatives measurable.

## 11. Increase canonical-profile support without cloning the canonical set

**Observed baseline:** 3/60 exact coarse-profile hits, all in easy; medium and hard had zero support.

**Decision:** include exact canonical-scale `(height, width, palette-size)` profiles in all bands while retaining larger scenes and dynamic object counts. This produced 16/60 exact hits with support in every band.

**Rejected alternatives:**

- Generate only exact canonical profiles. That would shrink size and object-count variation.
- Optimize solely for the profile score. The old generator’s real thin-shape failure demonstrates that dimensions and palette size are not sufficient.

**Probe/evidence:** `checks/before/checks/f65705efd235_before_profile_floor.json`; `checks/after/checks/f65705efd235_after_profile_floor.json`.

**Limitation:** the framework counts palette size including background, while the generator’s `n_rects` counts nonzero colors. Reports should not conflate the two.

## 12. Retain a cheap future-agent probe

**Decision:** add `workspace/probe_generator.py`. It checks all five canonical pairs, exact boundary overrides, generated counts, thin/overlap/hollow witnesses, rival disagreement, color and profile histograms, and three-example schedule windows. It writes JSON and exits nonzero on any error.

**Rejected alternative:** rely only on the full battery. The battery is authoritative but slower and less convenient for iterating on a single generator.

**Probe/evidence:** `checks/logs/high-volume-probe-final.log`; `checks/f65705efd235-probe-final.json`.

**Limitation:** it imports task-local implementation hooks and is intentionally not a generic cross-task checker.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-33e7e4d5ef69bf24:v0001`. Disposition: **no_issue**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `df598a4c9f22f38e6fec481d948022bf5f82bb8a32b8f6c31c1b6eb9500b2fb4`. At disposition, audited bytes match the current source.

### Current decision

Reported32tests+semantic and600cases/12profiles clean against declared rivals. Scoped inherited battery incomplete is not failed audit; no universal proof. Bounded reviewer-reported assessment only; other findings/source versions unchanged. Evidence=/home/user/Desktop/ARCpuzzles/var/review/new-return-tools-review/tool-disposition-proposals-nine.json sha256=76a7ea73fa5513ccc75ba5c5d6aad9abc549b59dfa65563ac320261676fd2870

### Assessment or prior finding

## f65705efd235

**No issue found in the checked domain.** The assigned generator SHA-256 was `df598a4c9f22f38e6fec481d948022bf5f82bb8a32b8f6c31c1b6eb9500b2fb4` and matched the inspected source.

The scoped audit command passed 32/32 task tests and the semantic gate. A fresh task-local probe generated 600/600 requested cases—200 per difficulty band—across twelve exact profiles. All 600 cases contained a lawful two-cell-thick rectangle, an overlap, noncorner outline cells, and a background-preserving strict interior; 300 contained more than two rectangles. The corresponding four always-applicable rivals were refuted 600/600 times, and the “process only two colors” rival was refuted on all 300 cases where more than two rectangles occurred. Five canonical labelled pairs were also checked, every ARC color 1–9 appeared in the sample, and there were no probe errors.

Evidence: `checks/audit-f65705efd235.console.log`, `checks/audit/f65705efd235/probe.json`, and `checks/audit/f65705efd235-combined/checks/f65705efd235_audit_semantic_gate.json`.

Limit: this is finite evidence against the target's declared rivals and sampled profiles, not a proof against undeclared shortcuts. The generated full-battery summary labels the run “incomplete” because only the scoped audit stages were requested; the command-level audit result itself passed.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
