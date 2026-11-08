# Working notes: ff5ef89054d2

## Review `review-ce3514cdbd093a4f`

The v3.0.0 ordered production lessons were identifiable, but the required query-rotation smoke test found 8 ambiguous rotations out of 48. In those rotations the only decoy-bearing pair became the query, leaving three demonstrations compatible with the canonical-fitting shortcut `expand_all_nonzero`.

Version 3.1.0 changes profiles 3 and 4 from zero to one connected decoy. Profiles 2..5 now contain decoys, while profiles 0 and 1 retain the strict canonical-like floor (2/6 = 0.333, above `MIN_STRICT_FRAC = 0.30`). Any four consecutive labelled pairs therefore contain at least two decoy scenes; holding out one pair still leaves a negative demonstration.

The review also:

- migrated canonical test loading to `reviewer_support.find_root` / `canonical_pairs` for portable task-test layouts;
- added a regression over all bands, schedule starts, and four possible query positions;
- required every declared semantic witness to map to at least one named disagreeing rival, removing two distribution descriptors that were not semantic rival witnesses;
- left the canonical Racket rule and canonical puzzle row unchanged.

Measured final evidence: 17 focused tests passed; the 12-stage battery passed; required rotations were 0/48 ambiguous; a 300-lesson census produced 1,200/1,200 unambiguous rotations and 1,200 unique inputs. The finite rival set does not prove identifiability against every possible program. The default schedule still correlates decoy presence with profile ID, although the 11,790-draw override matrix exercises both decoy values across every boundary mode.

Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.
## Current reviewer considerations

Source SHA-256: `bd5b58443f7a291285169a8f6ff489f3e698149006162a7290869a1de00ec236`.

# Decisions for `ff5ef89054d2`

## D1 — Treat query rotation as the real defect

**Choice.** Repair the lesson schedule rather than the individual rule implementation.

**Rationale.** Canonical outputs, the Python mirror, ordinary ordered lessons, and the baseline 12-stage battery were already correct. The reproducible failure was episode-level: 8/48 required rotations left `expand_all_nonzero` compatible with all demonstrations but different on the held-out query.

**Rejected alternatives.** Weakening the rotation gate would preserve ambiguous training examples. Changing the Racket rule would be incorrect because the authority already expresses the intended isolated-marker predicate. Increasing `EXAMPLES_NEEDED` from three to four would spend more context and still avoid the actual requirement that any labelled pair may become the query.

**Probe.** `checks/rotation-before/checks/ff5ef89054d2_before_semantic_gate.json` and the task-local regression `test_every_query_rotation_identifies_the_rule`.

## D2 — Add decoys to profiles 3 and 4

**Choice.** Use the six-profile decoy sequence `0,0,1,1,1,1`.

**Rationale.** Every cyclic four-pair bundle now contains at least two decoy scenes. Removing any one query therefore leaves at least one negative demonstration against expanding connected cells. This is the smallest production-distribution change: only two profile fields change.

**Rejected alternatives.** Making every profile contain a decoy would eliminate strict canonical-like draws and violate the declared 0.30 floor. Creating a special non-production contrast pair would not protect ordinary lessons. Filtering the decoy pair out of query position would encode an ordering dependency rather than teach the rule.

**Probe.** `checks/tdd-red/result.json`, `checks/rotation-after-v2/checks/ff5ef89054d2_after_semantic_gate.json`, and `checks/lesson-census.json`.

## D3 — Preserve two strict canonical-like profiles

**Choice.** Keep profiles 0 and 1 unchanged.

**Rationale.** Their 2/6 share is 0.333, above `MIN_STRICT_FRAC = 0.30`, while profiles 2–5 provide the contrastive decoy evidence. The final profile-floor and distribution stages passed.

**Rejected alternative.** Moving all negative evidence into canonical-like profiles would unnecessarily distort public morphology.

**Limitation.** Default decoy presence remains correlated with profile ID. The 11,790-draw override matrix proves the declared cross-product remains available, but default lessons do not independently randomize this axis.

## D4 — Keep only semantic witnesses with executable rivals

**Choice.** Remove `two_marker_scene` and `repeated_marker_color` from `SEMANTIC_WITNESSES`; retain the underlying variation and observables.

**Rationale.** They describe distribution coverage but did not identify a wrong transformation and had no `WITNESS_RIVALS` mapping. Keeping them as semantic witnesses produced an advisory warning despite otherwise clean required rotations. A red regression now requires every semantic witness to name a disagreeing rival.

**Rejected alternative.** Inventing arbitrary rivals solely to satisfy metadata would weaken the meaning of a semantic witness.

**Probe.** `checks/tdd-red-witnesses/result.json` and `checks/task-tests-green-v2/result.json`.

## D5 — Make focused tests portable

**Choice.** Replace the fixed `Path(__file__).parents[...]` canonical-data guess with `reviewer_support.find_root` and `canonical_pairs`.

**Rationale.** The supported isolated task-test stage failed before pytest because the copied test file ran at a different depth. The shared reviewer helper is the packet’s intended stable interface.

**Probe.** `checks/task-tests-before/result.json` versus `checks/task-tests-green-v2/result.json`.

## D6 — Do not alter authority or canonical data

**Choice.** Leave rule hash `d4b2121f30a4`, the canonical Racket source, and `puzzles.jsonl` unchanged.

**Rationale.** The defect was generation/curriculum coverage, not label semantics. Rule smoke and authority-sync stages passed before and after.

## D7 — Audit `32169a05c213` as clean in the checked domain

**Choice.** Re-run its source-bound cyclic rival probe rather than infer from retained notes alone.

**Rationale.** Across 3 bands × 100 seeds × 4 starts = 1,200 lessons, all eight declared competitors were refuted by the demonstrations and none remained query-ambiguous.

**Limitation.** This does not enumerate undeclared programs.

**Probe.** `checks/audit/32169a05c213/cyclic_probe.py` and `cyclic_report.json`.

## D8 — Report, but do not repair, `d292e3214bb1`

**Choice.** Reproduce the retained fixed-size shortcut with a fresh Racket application and leave the audit target unchanged.

**Rationale.** Audit duties require a source-bound finding, not a cross-task fix. At seed 21, “recolor every size-4 red component” fits all three demonstrations and all five canonical pairs, then disagrees with the authority on the size-5 query component.

**Probe.** `checks/audit/d292e3214bb1/shortcut_report.json`, `racket.json`, and `rival.json`.
