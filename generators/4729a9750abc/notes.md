# Current notes: `4729a9750abc`

## Intended rule and authority

Each of two or three aligned hollow color-9 frames has a rank key above (`2` smallest, `3` largest) and a transform key left (`3` identity, `4` clockwise, `5` left-right, `6` half-turn). Select the keyed interior same-color 4-connected component, crop it, transform it, then pack selected pieces left to right with one blank column and vertical centering. Canonical Racket authority is unchanged and pinned by `RULE_HASH = "12e5396a1c4e"`.

## Current distribution

Version `3.0.2` exposes four exact observable axes: `n_frames` 2–3, `frame_h` 8–9, `frame_w` 7–8, and `n_components` 2–3. Canonical 8×7 geometry is weighted but 9×8 remains supported. Ordinary inputs use connected asymmetric size-3/4/5 components with distinct sizes; the validator also accepts lawful one-component canonical interiors.

A seed-hashed period-4 schedule emits three 3-frame scenes and one 2-frame scene in every four consecutive samples. This replaced independent frame-count sampling after a 300-lesson census found four production and fifteen query-rotation ambiguities for the `first_two_frames_only` rival. The retained witness is easy seed `3758003496`, samples 44–47; see `counterexamples/review-ddcbd409ea699054/first-two-frames-lesson.json`.

The scheduled default value is recorded through a keyed singleton `GenCtx.draw_choice`; this repaired an intermediate provenance failure without changing output support. Three width-8 frames use a one-column gap so every legal axis combination remains within ARC's 30-column limit.

## Semantic contract

`EXAMPLES_NEEDED = 3`. Declared rivals are `first_two_frames_only`, `always_smallest`, `always_largest`, and `ignore_transform`; executable witnesses and `lesson_identifiable` check labels and refute each rival. Final source-bound evidence: 35/35 task tests, 12/12 battery stages, 300/300 production lessons and 1,200/1,200 query rotations with zero declared-rival ambiguity.

## Known limits

These are finite checks against named rivals, not universal identifiability. Generated shapes cover a controlled subset of lawful geometry. Difficulty changes layout randomness rather than defining a calibrated complexity ladder. No canonical/Racket data changed.
## Current reviewer considerations

Source SHA-256: `7e60d5b4d4f2b05024e86e305971a353532a59b8ff739bb3d6cd95df09deb871`.

# Decisions for `4729a9750abc`

## D1 — Keep the canonical authority unchanged

**Choice.** Pin `RULE_HASH = "12e5396a1c4e"`, implement a pure-Python mirror for validation/testing, and leave the canonical Racket rule and canonical JSONL untouched.

**Rationale and probe.** All five labeled canonical pairs are accepted by the repaired parser and reproduced by the independent workspace oracle. The final rule-smoke, Racket lint, and authority-sync stages are green.

**Rejected alternative.** Editing the authority to accommodate the old generator was rejected because the baseline distribution—not the canonical transformation—was defective.

**Failure mode/limit.** The Python mirror is supporting evidence only; Racket remains authoritative.

## D2 — Replace eight misleading axes with four exact structural axes

**Choice.** Advertise only `n_frames ∈ {2,3}`, `frame_h ∈ {8,9}`, `frame_w ∈ {7,8}`, and `n_components ∈ {2,3}`. Unknown, non-integer, Boolean, and out-of-range overrides fail explicitly. `observe_overrides` recovers every declared value.

**Original choice.** Version 2.0.1 advertised `ch_h`, `ch_w`, palette aliases, fixed-token position/density axes, and ordinary “textures” that included malformed negative fixtures. Several values never influenced output.

**Rejected alternatives.** Keeping aliases for compatibility was rejected because it would preserve dead controls. Retaining malformed fixtures in ordinary support was rejected because missing keys and tied ranks are not lawful edge cases for this task.

**Probe.** `test_exact_overrides_are_total_observable_and_lawful`, `test_invalid_or_unknown_overrides_are_rejected`, and the final override gate.

## D3 — Parse the task structure, not palette symptoms

**Choice.** `self_check` now requires exactly two or three equal-sized, aligned hollow color-9 frames; exactly one valid rank key above and transform key left of each frame; one to three interior same-color 4-connected components with distinct sizes; and no unexplained nonzero cells outside the documented structure.

**Rationale.** The baseline merely checked that color 9 and some nonzero cells existed, so missing keys, tied ranks, and outside noise passed.

**Canonical accommodation.** The parser accepts one-component canonical interiors, while the ordinary sampler deliberately emits two or three components. This separates lawful authority support from the richer generated teaching distribution.

**Limit.** The parser encodes the documented task grammar; novel but equivalent encodings outside that grammar are rejected intentionally.

## D4 — Make canonical profiles reachable without cloning examples

**Choice.** Weight 8×7 frames three-to-one over 9×8 alternatives. Three 8×7 frames with two-column gaps produce the canonical 12×29 envelope; connected asymmetric size-3/4/5 shapes, shuffled colors, key positions, and transforms supply variation.

**Rationale.** The baseline generated widths 20–22 and hit 0/60 canonical profiles. Weighted geometry repairs support while avoiding a corpus dominated by one canvas.

**Rejected alternative.** Always emitting the exact canonical dimensions was rejected because it would unnecessarily collapse geometry support.

## D5 — Preserve all legal joint-axis combinations within ARC limits

**Choice.** Use a one-column inter-frame key gap only when `n_frames=3` and `frame_w=8`; all other cases use two columns.

**Rationale.** The first rewrite made the individually legal combination 3×8 produce a 32-column input. The reduced gap keeps the maximum at 30 columns without declaring an artificial incompatibility.

**Probe.** `test_all_declared_axis_combinations_stay_within_arc_limits`; `checks/self-review.json` reports all 16 combinations clean and a 13×30 maximum.

**Rejected alternative.** Marking 3×8 incompatible was rejected because the geometry can be represented lawfully.

## D6 — Declare executable rivals and schedule complete-rule witnesses

**Choice.** Declare four pure rivals: first two frames only, always smallest, always largest, and ignore transform. Require three demonstrations. Schedule frame counts so every four consecutive samples contain exactly three 3-frame scenes and one 2-frame scene, with a seed-hashed phase.

**Original attempt and reversal.** The first repaired sampler drew frame count independently. A 300-lesson census found four production ambiguities and fifteen rotation ambiguities, all caused by `first_two_frames_only`; seed `3758003496`, easy samples 44–47 is the retained minimal witness. The schedule replaced that choice.

**Why this schedule.** It preserves ordinary support for both frame counts while ensuring that removing any one pair as the query still leaves at least two 3-frame demonstrations. A constant three-frame sampler would teach the rule but erase lawful two-frame support; an independent random sampler did not guarantee teachability.

**Probe.** `test_four_pair_schedule_is_identifiable_under_every_query_rotation`, the compacted failure report, and the final 300-lesson/1,200-rotation census.

**Limit.** Passing four named rivals does not prove unique induction against every possible program.

## D7 — Record scheduled values through `GenCtx`

**Choice.** The default schedule is recorded with `ctx.draw_choice("n_frames", (scheduled_value,))`; explicit overrides retain `(2,3)` as legal options.

**Rationale.** Computing the schedule outside `GenCtx` produced correct grids but failed provenance checks in 90/3,150 override draws. The keyed singleton draw preserves deterministic scheduling and exact auditability.

**Probe.** `test_default_frame_schedule_retains_keyed_draw_provenance` and the final override stage.

## D8 — Let difficulty vary layout, not the rule

**Choice.** Difficulty contributes to named RNG streams for key positions, shape variants, and colors; structural axes and semantics remain shared.

**Rationale.** The first rewrite made easy/medium/hard byte-identical. Band salt produces observable variation without introducing a separate rule or unsupported difficulty promise.

**Limit.** Difficulty is distributional variety, not a calibrated monotonic complexity scale.

## D9 — Use an independent test oracle

**Choice.** Place parsing/oracle helpers in `workspace/reference_probe.py` and load the generator under test through `GENERATOR_UNDER_TEST`. Tests do not call production parsing or solving helpers to establish expected behavior.

**Rationale.** An implementation-tested-by-itself would miss shared parser/transform errors. The final self-review found zero mismatches over 128 generated cases and five canonical pairs.

## D10 — Reprepare the exposed solve after the last source change

**Choice.** Preserve the earlier exposed solve under `checks/prior-solve/<old-hash>/`, then prepare and finish a new episode from final generator bytes.

**Rationale.** Solve evidence is source-bound. Copying the old episode forward would falsely imply it exercised the final scheduler/provenance source.

## Known limits

- The final census covers 300 production lessons, 1,200 query rotations, 1,200 unique inputs, and the declared rival set; it is not a proof against undeclared rules.
- The deterministic period guarantee concerns consecutive four-pair lessons assembled by the production sampler. Different lesson assembly policies require their own check.
- Generated components occupy a controlled connected size-3/4/5 subset. The validator accepts broader lawful canonical geometry, but ordinary sampling does not cover every possible shape.
- The Racket authority was not modified or reinterpreted.
