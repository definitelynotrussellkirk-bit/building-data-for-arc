# Working notes: e73c86cb45ad

## Review 2026-10-07

Baseline version 2.1.0 had a false override surface: palette/texture controls were inert, unknown keys were accepted, and globally legal dimensions could be rejected by difficulty-specific ranges.  The selected Racket rule itself matched all canonical pairs and was left unchanged.

Version 3.0.0 exposes six exact, pixel-recoverable axes (`grid_h`, `grid_w`, `shape_size`, `match_rotation`, `match_order`, `n_distractors`), validates requests strictly, and uses constructive separated placement.  References have four unique rotations; distractors have the same size but lie outside the reference rotation class.

All five canonical pairs admit the wrong `first_candidate` rule.  The default order schedule therefore guarantees a later-position match in every three-example window.  The production/rotation census and an exhaustive 912-start-per-band probe found no surviving declared rival.

Final generator SHA-256: `da555463415e9229e5b468864d3d6f5acf67b98cd81ead573204313ee77282c5`.
Final battery: 12/12 green.
Selected tests: 39/39 pass.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `da555463415e9229e5b468864d3d6f5acf67b98cd81ead573204313ee77282c5`.

# Decisions for `e73c86cb45ad`

## D1 — Keep the Racket authority unchanged

**Decision.** Preserve the selected canonical rule and bind the generator to normalized `RULE_HASH = "a405585a6a23"`.

**Rationale.** Canonical Python-oracle checks and live Racket execution agreed on all five canonical pairs.  The observed failures were in input generation, override semantics, and teaching coverage—not label authority.

**Alternatives rejected.** Rewriting the rule for style or to match a narrower sampler would add authority risk without repairing the contract.  The final authority-sync and rule-smoke stages remain green.

**Failure mode/limit.** The task-local `rule_mirror` is diagnostic only; Racket remains label authority.

## D2 — Replace the advertised controls rather than preserve inert names

**Decision.** Advertise exactly six controls recoverable from returned pixels:

- `grid_h`: 10–16
- `grid_w`: 11–16
- `shape_size`: 4–7
- `match_rotation`: 0–3 clockwise turns
- `match_order`: `first|later`
- `n_distractors`: 1–2

Every key is type/range checked before generation, unknown keys are rejected, and all legal values remain legal in every difficulty band.

**Rationale.** An exact axis is useful for dataset control only when the requested value is observable and replayable.  The baseline `palette_kind`/texture surface was inert or misleading, while dimensions were restricted after choosing a band.

**Alternatives rejected.** Keeping compatibility aliases would preserve silent no-ops.  Reintroducing arbitrary palette controls was unnecessary because object colors are semantic roles and the canonical palette already has constrained support.

**Probe.** `tests/test_generator.py::test_exact_override_cartesian_is_observable_and_lawful_in_every_band` covers all 64 endpoint combinations in each of four bands (256 generated cases), and invalid/unknown inputs have dedicated negative cases.

## D3 — Use constructive four-zone geometry

**Decision.** Place the reference and up to three candidates in separated 4×4 corner zones, with the top-right singleton reserved as the output-color key.

**Rationale.** Constructive placement makes collision freedom and component count explicit, avoids rejection sampling, and works across every legal grid dimension.  Random offsets within each zone preserve local positional variation.

**Alternatives rejected.** Free placement with retries increased the chance of touching/merging components and made extreme override combinations brittle.  A fixed exact offset would be easier to exploit and less diverse.

**Failure mode/limit.** Coarse zone membership is regular.  The schedule therefore moves the true match across candidate positions, and selection still requires shape comparison because same-size distractors occupy the other zones.

## D4 — Use four-orientation reference shapes and same-size nonmatches

**Decision.** Enumerate connected polyominoes of size 4–7 that fit 4×4 slots; choose references with four distinct rotations, choose distractors outside the reference rotation class, and rotate distractors independently.

**Rationale.** Four distinct orientations make `match_rotation` pixel-recoverable.  Equal cell counts remove size as a proxy, while a different rotation class guarantees exactly one match.

**Alternatives rejected.** Symmetric references would make multiple requested rotations visually identical.  Smaller/larger distractors would let a size-only rule solve the generated data.  Reflections were not added because the selected rule recognizes rotations only.

**Probe.** `observe_overrides`, `self_check`, the independent oracle, and live Racket parity jointly verify unique match, requested rotation, and label correctness.

## D5 — Preserve canonical profiles while teaching against the canonical shortcut

**Decision.** Begin the default size stream with the five public input dimensions and use two distractors there, reproducing the public six-color profiles.  Use a three-position order cycle `first, later, later`; every contiguous three-example lesson includes a non-first match.

**Rationale.** All five canonical pairs place the true match first, so the wrong rule “crop/recolor the first candidate” fits the entire canonical set.  A non-first demonstration is therefore required teaching evidence, not optional diversity.

**Alternatives rejected.** Pure random order could still produce all-first three-demo windows.  Always-later would remove a legitimate branch and make “always second” a new shortcut.  Increasing the demonstration count was unnecessary once every three-demo window contains a witness.

**Probes.** The source-bound census materialized 300 production lessons and tested 1,200 held-out query rotations with zero declared-rival ambiguity.  `workspace/lesson_schedule_probe.py` exhausts all 912 cyclic starts per band and reports zero failures.

## D6 — Differentiate difficulty without shrinking the legal contract

**Decision.** Difficulty changes the default shape-size schedule through band-specific offsets; it does not alter override validity.

**Rationale.** The first rewrite accidentally produced byte-identical defaults across easy/medium/hard because `GenCtx` does not automatically salt every scheduled draw by difficulty.  A regression test reproduced that root cause.  Explicit offsets now make all three defaults distinct for each sampled index while preserving the same exact-control domain.

**Alternatives rejected.** Band-specific min/max ranges recreate the original global-domain contradiction.  Difficulty-dependent hidden palettes would not be a recoverable semantic control.

**Failure mode/limit.** Difficulty here is distributional variation, not a calibrated proof of human or model hardness.

## D7 — Add portable, source-bound tools

**Decision.** Keep two reusable task-local tools:

- `workspace/reference_probe.py`: independent component/rotation oracle, canonical audit, deterministic distribution census, and optional live Racket parity.
- `workspace/lesson_schedule_probe.py`: exhaustive cyclic-start lesson validation over the default schedule period.

**Rationale.** The general battery samples broadly but does not exhaust a small deterministic schedule or guarantee a standalone task probe remains runnable in a stripped packet.

**Portability repair.** A failing CLI regression showed `puzzle_generators.rule_wrap` still imports the legacy module name `scripts.comment_solutions`, while the packet stores it under `shared/tools`.  The probe installs an explicit local alias before invoking Racket, without changing shared runtime code or replacing authority.

## Remaining limits

The semantic checks test one declared canonical-fitting rival (`first_candidate`) plus structural invariants.  They do not prove the lesson uniquely specifies the rule among all programs.  Grid dimensions, shape sizes, and coarse zones are intentionally bounded to the domain tested here; extrapolation outside those bounds is unmeasured.  The post-repair solve is evidence that the visible curriculum is understandable, but it is not blind because rule exposure occurred earlier during repair.
