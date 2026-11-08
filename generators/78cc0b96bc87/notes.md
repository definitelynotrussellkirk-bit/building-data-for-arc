# Review notes: 78cc0b96bc87, v2.1.0

Final generator SHA-256: `0a62551caf756250069d4831784c5d76b04e2bea84a620d638c85f4e4dd2ad6c`.
The canonical Racket authority and pinned rule hash `5ed55d63a700` are unchanged.

The rule is a left-anchored two-color checkerboard inside one hollow rectangular
frame. The two strict-interior seeds share a row: the left seed supplies the
interior top-left/even-parity color and the right seed supplies the odd-parity
color. Both seeds must already lie on their output parity, so labels never
silently recolor the cue cells.

The v2.0.0 generator accepted canonical frame heights 6–8 in its strict grammar,
but its declared axis, override contract, and sampler stopped at 7 even though a
canonical input has an 8-row frame. Version 2.1.0 extends `frame_h` to 6–8 in all
three places. No other axis, layout, palette rule, schedule, or output rule was
changed. A focused regression test covers exact height-8 generation in every
band and every seed layout.

Final evidence:

- all 12 after-battery stages passed;
- all 7 selected task tests passed (the new test first failed against v2.0.0);
- a 900-draw distribution probe had 900/900 valid strict inputs; hard draws now
  included frame height 8 in 214/300 cases;
- 300/300 ordered three-demonstration lessons were identifiable against all six
  declared competitors;
- arbitrary hold-one-pair-out rotation is intentionally **not** claimed:
  308/1,200 rotations were ambiguous, chiefly because the scheduled witness may
  become the query. The production policy is three consecutive demonstrations
  followed by the next generated query.

Strongest retained canonical-fitting shortcut: treat the literal top-left
interior cell as the phase key, falling back to the numerically smaller seed
color when that cell is empty. The shifted-pair schedule refutes it; the exact
Racket-checked witness is under `checks/question-generator-shortcuts/`.

Known limits: the finite rival set is not a universal induction proof, the
curriculum is order-sensitive, and exact overrides can deliberately remove a
scheduled witness. No unresolved repair blocker remains.
## Current reviewer considerations

Source SHA-256: `0a62551caf756250069d4831784c5d76b04e2bea84a620d638c85f4e4dd2ad6c`.

# Decisions — review-675f7467c23483e3

## D1 — Restore the missing canonical frame-height axis endpoint

**Prior choice:** v2.0.0 declared and sampled `frame_h` only in 6–7.
**Problem:** the fifth canonical input has an 8-row frame, and the existing
strict recognizer already described 6–8 as canonical support.
**Decision:** change the axis declaration, explicit override validator, and
`draw_int_diff` upper bound to 8; bump to v2.1.0.
**Rejected alternatives:**

- Leaving the sampler unchanged would preserve a real canonical coverage hole.
- Allowing height 8 only through an override would make the contract exact but
  would not improve the ordinary input distribution.
- Broadening unrelated geometry or seed rules would add risk without addressing
  the observed defect.

**Evidence:** `checks/task-tests-red/` captures the pre-change failure;
`checks/task-tests-portable/` and the 12-stage after battery capture the final
pass. Canonical and final source hashes are recorded in `RESULTS.json`.

## D2 — Keep difficulty weighting, not uniformize every band

`draw_int_diff` already provides difficulty-aware integer support. Extending its
upper bound gives easy draws 6/7, medium draws 7, and hard draws 7/8 under the
observed deterministic sample. I retained that behavior: the repair should add
the tallest canonical frame without making every difficulty visually identical.

A 300-draw-per-band probe (`seed = 400000 + sample_index`, indices 0–299) found:

- easy: height 6 = 224, height 7 = 76;
- medium: height 7 = 300;
- hard: height 7 = 86, height 8 = 214.

All 900 inputs passed `self_check` and `strict_canonical_like`; each seed layout
appeared exactly 100 times per band. The probe is
`checks/frame-height-census.json`.

## D3 — Do not change the Racket authority or inferred rule

The generator's independent Python mirror agrees with all five canonical pairs,
and the final rule/authority smoke checks passed. The defect concerned reachable
input geometry, not output semantics. `RULE_HASH` therefore remains
`5ed55d63a700`; no Racket file changed.

## D4 — Add a focused, portable regression and preserve the red phase

The new test requests `frame_h=8` in easy/medium/hard and in canonical, shifted,
and spaced seed layouts, then checks grammar and observable exactness. It failed
for the intended reason before implementation (6 passed, 1 failed) and passed
afterward (7/7). I also replaced the task test's private `scripts.*` import with
`reviewer_support.canonical_pairs` and `find_root` so the returned test works in
the isolated runtime and fresh replay.

## D5 — Preserve the ordered three-slot teaching policy

The production assembly uses three consecutive demonstrations followed by the
next pair as query. Every three-slot demonstration window contains canonical,
shifted, and spaced layouts, plus the color-order and frame-position variation
required by `lesson_identifiable`. The final census found 0/300 ambiguous
production lessons against the six declared competitors.

I did **not** claim arbitrary query permutation. Holding out every materialized
pair produces 308/1,200 ambiguous rotations because a necessary scheduled
witness can become the query. The first required-policy census correctly exited
nonzero and is retained; the same source was rerun with
`--rotation-policy diagnostic`, matching the documented downstream policy.
Changing the schedule to support all rotations was rejected as unrelated scope
for a one-endpoint geometry repair and would require a larger curriculum design.

## D6 — Retain the strongest canonical-fitting shortcut as executable evidence

The strongest simple rival is `top_left_cell_is_key`: use the literal top-left
interior cell as checkerboard phase; if it is empty, use the smaller numeric seed
color. It fits the canonical demonstrations because their left cue occupies that
cell. The exact shifted-pair witness in
`checks/question-generator-shortcuts/` has left/right seed colors 7/5 away from
the corner. The rival chooses 5 while the intended rule chooses the left seed 7,
causing 42 differing cells. The supported Racket `apply` output agrees with the
intended rule.

## D7 — Audit findings stay findings-only

Per assignment, I did not edit either audit target. For `ba29d14676d1`, I kept an
exact generated 3x11 noncanonical lattice accepted by `strict_canonical_like`.
For `1484fc8ec47b`, I retained one Racket-labelled rotation where
`largest_room` fits all three demonstrations and differs on the query. These are
reported in `AUDIT.md`, not mixed into the selected-task repair.

## 2026-10-25 native parametric review `review-5af5df705f6335a0`

Production `generator.py` and canonical rule `5ed55d63a700` remain unchanged. The task-local native family lives in `workspace/parametric/` and has one exact canonical default plus one sequential alternative:

- `relay_rule=checkerboard_only` returns the selected canonical Racket program byte-for-byte.
- `relay_rule=marker_slice_relay` first completes the canonical left-anchored checkerboard inside the frame. Each external color-8 marker then selects a completed interior row or column, and Stage B copies that entire ordered slice into an equally long exterior relay lane ending at the marker.

### Current decisions

1. **Preserve exact canonical bytes as the default.** No approved production or canonical source was edited; the extension is isolated under the task-local promotion adapter.
2. **Make the relay depend on completed geometry, not sparse input cues.** Marker axes deliberately avoid both raw seeds. The selected source slice is therefore blank in the raw input but alternating after Stage A; the protected wrong-intermediate witness changes 6 final cells.
3. **Teach orientation and source semantics with two demonstrations.** The first two demonstrations contain horizontal and vertical relays and reject six canonical-only plus ten relay shortcuts before any query is observed.
4. **Keep query reveal independent and private.** The adapter supports 2–6 demonstrations and 1–4 independently generated, prefix-stable queries. The fourth query is 30×30, uses four marker-selected slices, touches every boundary, and has more than 120 nonzero output cells.
5. **Treat finite audits as bounded evidence.** The self-audit checks 32 declared rivals over four qualified episodes, not arbitrary-program uniqueness.

### Final reviewer evidence

- `checks/78cc0b96bc87-portable-tests/result.json`: 16/16 selected-task tests passed.
- `checks/78cc0b96bc87/qualification/`: two settings × seeds 0 and 17, four jobs, 32 protected-Racket label evaluations.
- `checks/78cc0b96bc87/replay-compare.json`: deterministic replay reproduced the program and execution hashes.
- `checks/78cc0b96bc87/self-audit.json`: four episodes, 32 declared rivals, 64 rival evaluations, zero demonstration survivors.
- `checks/78cc0b96bc87/public-preview/private/manifest.json`: four episodes and 16 sequential public views passed projection checks.
- `checks/78cc0b96bc87/causal/witness.json`: protected wrong-intermediate counterfactual changed 6 cells.

Reviewer status is **ready**. Exact-source owner integration, fresh owner qualification/acceptance replay, and any training-admission decision remain pending; `training_admitted` is false.

