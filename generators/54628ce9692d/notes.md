# Current review notes: 54628ce9692d

## Intended rule

A 13×13 modal-background scene contains 2–4 separated rigid color-1 pieces. Marker colors occurring exactly twice on different pieces define a connected docking tree. Infer each marker's outward port direction, translate the linked pieces so paired markers are cardinally adjacent, preserve all colors and orientations, then crop the assembled object. One unmatched marker may remain as a free endpoint.

## Current canonical source

- Generator version remains `3.0.0`; final generator SHA-256 is `abbc6a54d162305c73ba6f8aab2966816469df0f283c71a34c9a143abeaf0dcc`.
- `RULE_HASH` remains `9b6d1153ebca`; lawful generation was intentionally not rescheduled.
- The selected `racket_target.target_code` in both training and augmented authority records was aligned byte-for-byte to canonical source SHA-256 `9ddc1ad5a626057fc08c9394a736d0e06f1c3da45ce732d1908e62f36b8aa662`. Archival `raw_code` was preserved. This was a text-authority synchronization, not a semantic rule change.

## Repairs and decisions

1. Calls now require literal integer `seed` and non-negative literal integer `sample_index`; booleans, strings, floats, and `None` are rejected. Negative integer seeds remain lawful.
2. Exact controls now require literal integers in the declared domains: `n_pieces=2..4` and `background_color=2..9`. Unknown controls and invalid difficulties remain rejected.
3. The task now exposes an executable teaching contract: three demonstrations, 100% strict morphology, two witnesses, and two nearby rivals—cropping the scattered scene without assembly, and docking with a one-cell gap. Labels are checked against the independent Python rule mirror before rival scoring.
4. The helper `_placements(..., marker_step=1)` keeps canonical behavior at step 1 and supports the task-local parametric prototype at step 2. A 180-case before/after schedule comparison found zero lawful-output changes.

## Parametric proposal

`workspace/parametric/prototype.py` proposes hidden episode parameter `docking_distance ∈ {1,2}`. Distance 1 is byte-exact canonical behavior; distance 2 preserves the same objects, paired-marker tree, outward-port inference, transitive placement, and crop while leaving one background cell between paired markers. It is **proposed and unapproved**, with finite Racket-backed evidence only. Arbitrary unseen morphologies may collide at distance 2.

## Verification and open finding

The completed after battery is 12/12 green; focused review/prototype tests are 29/29 green. A 300-lesson census (100 per band) materialized 1,200 labeled pairs and 1,200 diagnostic query rotations with zero ambiguities against the two declared rivals. The inherited 414-line root fixture remains blocked in the portable task-test preflight because it derives canonical data from a fixed `__file__.parents[1]`; it is frozen by assignment and was not edited. New portable tests pass independently.

The prior audit `review-178145f097390980:v0001` was used only as a lead for that fixture-path defect; it was reproduced against the current packet. No other prior-return claim was treated as a current measurement.
## Current reviewer considerations

Source SHA-256: `abbc6a54d162305c73ba6f8aab2966816469df0f283c71a34c9a143abeaf0dcc`.

# Decisions for 54628ce9692d

## D1 — Preserve the canonical generator schedule

**Prior choice:** generator `3.0.0` used five published piece/topology profiles, D4 nuisance transforms, palette variation, and exact controls for piece count and background.

**Decision:** keep that lawful schedule and version unchanged. The measured defects were call validation, missing teaching hooks, and selected authority text—not a failure of lawful generated grids. A 180-case before/after comparison across all difficulties, piece counts 2–4, and backgrounds 2/5/9 found no output changes (`checks/valid-schedule-regression.json`). Changing the version or resampling would create needless data churn.

**Rejected alternative:** redesigning profiles or adding new morphologies during this repair. That would mix a broad distribution change with API and semantic-contract fixes, weaken attribution, and require new collision analysis.

## D2 — Enforce literal integer calls at the generator boundary

**Decision:** require `type(value) is int`, not `isinstance(value, int)`, for `seed`, `sample_index`, `n_pieces`, and `background_color`. Require `sample_index >= 0`; retain the full signed integer seed domain. Enforce exact control ranges `n_pieces=2..4` and `background_color=2..9` before `gen_ctx`.

**Reason:** the before linter reproduced 69 accepted malformed scalar calls, including booleans, strings, floats, and a negative sample index. Silent coercion/collision can duplicate or misindex training examples.

**Rejected alternative:** rely on `gen_ctx` coercion. It accepted the reproduced invalid public-call forms and did not provide a generator-local contract.

## D3 — Teach two nearby, executable alternatives

**Decision:** set the minimum to three demonstrations and require strict canonical morphology on all sampled inputs. Declare two rivals:

1. crop the separated pieces without assembling them;
2. assemble the correct marker tree but leave a one-cell gap.

Pair them with witnesses that prove the scene actually requires assembly and that canonical markers touch. Validate all supplied labels through `rule_mirror` before checking rival survival.

**Reason:** these alternatives preserve much of the visible structure and are plausible model shortcuts. They target the two central reasoning steps: composition and exact docking distance.

**Rejected alternatives:** superficial color-only or first-object shortcuts were less task-specific, while arbitrary rotations or a different graph topology would no longer be a nearby interpretation of the displayed family.

**Limit:** passing these rivals does not prove unique induction against every possible rule. The report and notes retain that scope explicitly.

## D4 — Synchronize selected authority text only

**Decision:** apply the generated `authority-sync --selected-only` proposal. Replace only selected `racket_target.target_code` with the canonical `program_solution`; preserve `raw_code` and the declared rule hash.

**Reason:** the before authority stage showed exact active-authority divergence despite sampled execution parity. Exact text binding is required for reproducible source hashes and future audits.

**Rejected alternative:** edit or discard archival `raw_code`. That would erase provenance and was unnecessary.

## D5 — Prototype `docking_distance`, do not promote it

**Decision:** build a task-local, unapproved parameter `docking_distance ∈ {1,2}`, selected once per episode. Distance 1 is exact canonical behavior; distance 2 changes only the translation step so equal-color marker cells are separated by one background cell.

**Why this parameter:** it changes the executed transformation while preserving the original objects, equality pairing, port inference, tree composition, and crop. It is small enough to infer from demonstrations and directly reuses the canonical Racket structure.

**Alternatives rejected:**

- changing marker/background colors is cosmetic;
- changing piece count or scatter changes inputs, not the rule;
- rotating pieces or changing graph pairing alters the family more substantially and introduces new orientation semantics;
- a larger distance range was unnecessary and raises collision risk.

**Evidence:** `checks/parametric/docking-distance-v1/report.json` covers values 1 and 2 with exact Racket programs, 10 canonical replays, two complete episodes, and rival checks. **Status remains proposed/unapproved.** Distance 2 may collide for unseen morphologies, so it is not wired into production.

## D6 — Use diagnostic query rotations, not a universal claim

**Decision:** run 100 production-sampled lessons per band with three demonstrations, one query, and every materialized pair held out once under `rotation-policy=diagnostic`.

**Reason:** downstream lessons are ordered, but rotation is a useful stress test. All 1,200 rotations were unambiguous against declared rivals.

**Limit:** rotations reuse each materialized four-pair bundle and do not enumerate every possible schedule start or undeclared hypothesis. The result is reported as finite diagnostic evidence.

## D7 — Keep the frozen fixture unchanged and report blocked aggregate tests

**Decision:** do not patch inherited `test_generator_54628ce9692d.py`. Add portable tests under the task's `tests/` directory and run them directly, while retaining the official preflight failure.

**Reason:** the assignment explicitly freezes the root fixture and assigns its migration to the library maintainer. Rewriting it would hide a portability defect and violate the review contract.

**Result:** 29 new tests pass; the official aggregate stage remains blocked before pytest. Completion is therefore reported as blocked rather than converting partial evidence into an aggregate pass.
