# Working notes: 678b4a951150

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `b7a21f8d76100fc5e14b820e2f93e0d08e8bea1b6cd885b1396028ec6dfa0535`.

# Decisions for 678b4a951150

## Scope and authority

The selected baseline was generator v2.0.0, SHA-256 `a0957534c88731244a4d764c746f51f4549106f7098b150b75729c0b3e151e10`. I used associated note `GNOTE-002784` (the equal-nonzero-gap shortcut) as a lead, not as current-source evidence, and reran all checks on the pinned baseline. The Racket authority remained unchanged at rule hash `f5f03a3a484b`; canonical parity, Racket lint, and authority synchronization were green before and after.

## Defect D1: missing boundary-row evidence

The canonical examples include decisive targets on the first/last row, but baseline generated placement did not schedule that fact. A plausible rival that fills only interior rows fit all four demos and changed the query in 7/5,000 easy, 6/5,000 medium, and 4/5,000 hard ordinary lessons. Seed 477/easy is retained in `checks/before/undeclared-rival-repro.json`.

**Decision.** Profiles 0 and 2 deterministically place their first target run on row 0 or the last row. The rival `interior_rows_only` and witness `boundary_row_target` are declared, connected, and tested. Two profiles rather than one keep the fact present under query rotation.

## Defect D2: missing interaction between target and color 6

The baseline randomized 6s independently. A rival that refuses to fill a target on any row containing a 6 fit all demos and changed the query in 7/5,000 easy, 3/5,000 medium, and 2/5,000 hard lessons. Seed 921/easy is retained in the same reproducer.

**Decision.** Profiles 0 and 2 require at least one 6 on a target row. The rival `target_rows_without_six` and witness `target_row_with_six` are declared. Placement preserves exact target/six counts and rejects accidental grammar changes rather than mutating labels.

## Defect D3: single-point 6-0-6 witness failed query rotation

The first repaired v2.1.0 source passed the ordered production lesson, but the required 300-lesson rotation census found 225/1,500 ambiguous held-out rotations. Every failure held out the only profile carrying `6,0,6`, leaving the canonical-fitting `equal_nonzero_gap` rival unrefuted. The failure is preserved under `checks/intermediate-v2.1/lesson-census.json.gz` with its restoration map in `lesson-census.compression.json`, and the test-first reproducer is `checks/tdd-rotation-red.log`.

**Decision.** Profile 0 now carries a `6,0,6` negative in addition to profile 2. This is the minimum deterministic change that makes every four-of-five rotation retain the color-specific refuter. The final census has 0/300 production ambiguities and 0/1,500 rotation ambiguities; the broader task-local probe has 0/6,000 ambiguous rotated queries across 1,200 cyclic-start windows.

## Distribution choices retained

- Preserve the four canonical height/width/target/six profiles and exact override ranges. Expanding global size or changing the black background would reduce task fidelity.
- Preserve the four-example profile cycle; difficulty rotates the starting profile but does not remove semantic coverage.
- Preserve negative orange structures: vertical `7-0-7`, adjacent `7,7`, longer horizontal gaps, dangling orange, and rows with multiple targets.
- Preserve exact counts. Required witnesses are placed constructively and every placement is reanalyzed; failed placements are retried rather than silently relaxing an invariant.
- Keep color 3 output-only and keep Python `rule_mirror` input-pure.

## Alternatives considered

Random resampling until witnesses happened to appear was rejected because it leaves low-frequency ambiguity and makes lesson quality seed-dependent. Putting every witness in every profile was rejected as unnecessary visual regularity and reduced diversity. Treating rotations as merely diagnostic was also rejected after the failure was reproducible; duplicating one negative witness was cheap and made the stronger contract pass.

## Tests and reusable tool

`tests/test_missing_lesson_witnesses.py` contains regression coverage for profiles 0/2, the two newly declared rivals, known ambiguous seeds, and every query rotation for representative seeds/bands. `workspace/lesson_rival_probe.py` dynamically loads all actual rival declarations, scans finite seeds, all configured cyclic starts, and optional query rotations, retaining bounded exact examples. Its limits are explicit: declared finite rivals and sampled seeds do not prove universal rule induction.

## Self-review for new restrictions/shortcuts

The repair does not alter dimensions, palette, target count, six count, output rule, or advertised overrides; it only constrains where existing legal cells occur in two profiles. A finite 100-seed × 3-band × 4-start probe produced 2,400 unique inputs from 1,200 windows and found no ambiguity or hook warning in 6,000 rotations, so the added witnesses did not collapse the schedule into duplicate scenes.

## Remaining limitations

No finite rival set proves uniqueness against all conceivable programs. The generator remains a candidate pending independent maintainer/monitor approval, and the post-repair solve has visible-only feedback; masked-query correctness is intentionally unknown. No rule-source change was needed or made.
