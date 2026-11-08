# Working notes: e4cb0224ca42

## Intended rule

On a fresh zero grid of the same shape, replace each solid monochromatic odd-by-odd rectangle by the union of its bounding-box middle row and middle column, preserving that rectangle's color. Objects are segmented by same-color 4-connectivity. Diagonal corner contact is lawful; cardinal contact is excluded so separate objects remain unambiguous.

Canonical authority is pinned by `RULE_HASH = "7798fb9f1ac0"`. The Racket rule was not changed in this review.

## Baseline finding and retained lead

I used prior return `review-5994a478cf362114:v0001` only as a lead, then reproduced against the pinned baseline SHA-256 `5073b90d0c44b4ab4f4517bbfb528fdf5ad64a551a572d03484be4669d80f6b8`.

The v3 sampler drew a requested rectangle count, attempted bounded random placements, silently skipped failed placements, and never compared requested with realized count. Easy seed 3, sample 0, `n_rects=2` returned one 3x7 rectangle and passed `self_check`. Prior choice: retry-and-drop with a one-cell diagonal moat. New choice: exact constructive placement and cardinal separation only. Reason: requested/observed drift and canonical train 0's lawful diagonal contact. Evidence: `counterexamples/silent-underfill-seed-3.json` and focused tests.

## Current design (v4.0.0)

- Public exact axes are only `grid_h` (7..14), `grid_w` (9..16), and `n_rects` (1..3). Dead aliases, palette metadata, texture degenerates, and fixed single-token axes were removed.
- Explicit override draws use strict integer validation. Unknown keys, coercive booleans/floats/strings, negative seed/index values, and unknown difficulties fail loudly.
- Override scenes use four constructive regions separated by a central background row/column. The requested count is always placed, then independently observed and asserted.
- Default lessons use four recurring canonical-profile templates (7x9, 9x11, 8x10, 9x11), randomized by reflection and color. Every default grid has two rectangles; any three consecutive profiles contain a non-square rectangle. Difficulty bands rotate colors through distinct bijections so the parameter is observable without changing the rule.
- `self_check` independently parses 4-connected components, requires 1..3 distinct-color solid rectangles with each dimension in {3,5,7}, and rejects cardinal contact. It accepts all four canonical inputs, including diagonal contact.
- `rule_mirror`, `observe_overrides`, `strict_canonical_like`, named rivals, executable witnesses, and `lesson_identifiable` are provided. The retained rivals are center-only, row-only, column-only, squares-only, and first-rectangle-only.
- I intentionally do not declare `LESSON_SCHEDULE_PERIOD`: the strict battery currently warns whenever that opt-in is not separately enumerated, and cannot consume the separate receipt. The task-local test still exhausts all four starts and every held-out query position.

## Evidence and limits

Task-local tests cover the original seed-3 failure, a 256-seed x 3-band x 3-count realization sweep (2,304 generated inputs), every public corner override, canonical inputs/outputs, strict call validation, deterministic fresh returns, targeted malformed shapes, all four schedule starts, and all query rotations.

Finite rivals are not a proof of unique human induction. Defaults intentionally emphasize canonical-sized two-object lessons; the wider 1..3 object and 7..14 x 9..16 envelope is exercised through exact overrides. Colors are distinct by design, so this generator does not teach repeated-color object separation. The output rule is only promised on the documented solid odd-rectangle manifold.

Open evidence is recorded in `WORK/checks/`; final battery and larger lesson-census results are summarized in the top-level review rather than copied here.

## Final source-bound results

Final generator SHA-256 is `1c86e2a97f9f050cc7fb89a2f210a6d961d4466a982afe70cd6c7773020d6b9b`. The strict after battery is 12/12 green, portable task tests are 29/29 green, and the 300-lesson census reports 0 production ambiguities and 0/1,200 ambiguous query rotations. The post-repair visible solve is frozen against the same generator hash.

<!-- arcpuzzles-current-audit-assessment:start -->
## Current bounded audit assessment

Return: `review-5994a478cf362114:v0002`. Disposition: **resolved**. Evidence basis: `reviewer_reported`.

Audited source SHA-256: `5073b90d0c44b4ab4f4517bbfb528fdf5ad64a551a572d03484be4669d80f6b8`. At disposition, the audited source differs from the current source; this assessment covers audited bytes only.

### Current decision

Resolved the specific silent-underfill finding against owner-accepted review-ce6170c44df213aa:v0001, generator SHA1c86e2a97f9f050cc7fb89a2f210a6d961d4466a982afe70cd6c7773020d6b9b and unchanged rule7798fb9f1ac0. Selected source now places the exact count constructively and independently compares observe_overrides with requested grid_h/grid_w/n_rects. Task-owned counterexamples/silent-underfill-seed-3.json binds baseline5073b90d to the repaired requested2/observed2 witness; focused tests preserve regression, reviewer reports2304 exact-count cases and12/12 battery. This explicit closure is reviewer-reported repair evidence plus source inspection, not a fresh owner sweep or universal semantic qualification.

### Assessment or prior finding

## e4cb0224ca42

**A2 — reproduced silent placement underfill.**

Source SHA256:
`5073b90d0c44b4ab4f4517bbfb528fdf5ad64a551a572d03484be4669d80f6b8`.
Rule SHA256:
`ddb1edd2986f31a1aa1061cc396ee29b96edaac71c68f2b61deae3dd4e51a2bc`.

The sampler draws a requested number of solid odd-sized rectangles, but after
bounded placement attempts may return fewer. The validator accepts the resulting
input and does not compare realized count with the sampled request.

Measured seeds **0–255**, sample index **0**, each of easy/medium/hard:

| Band | Draws | Underfilled | Underfilled inputs accepted by validator |
|---|---:|---:|---:|
| easy | 256 | 52 | 52 |
| medium | 256 | 38 | 38 |
| hard | 256 | 7 | 7 |
| Total | 768 | 97 | 97 |

There were **761 unique inputs** across the 768 draws. The first concrete witness
is **easy, seed 3, sample index 0**: request **2**, realize **1**, self_check `[]`.
The retained input is 8×11 with one color-5 3×7 rectangle. The actual Racket
output is the corresponding central cross. This is silent distribution/metadata
drift, not evidence that those Racket labels are wrong. Eight witnesses per band
are retained (24 total), including requested/realized counts and exact grids.

**Suggested separately scoped repair:** construct a feasible packing before
placing, or retry/reject the whole draw visibly when the requested count cannot
be realized. Expose requested and observed count and assert equality. Do not
patch metadata to hide dropped rectangles. This review's main generator uses
constructive slots, but this audit target was intentionally left unchanged.

The disposition records an explicit decision. It does not imply a fresh execution, universal correctness, closure of other findings, or training admission.
<!-- arcpuzzles-current-audit-assessment:end -->
## Current reviewer considerations

Source SHA-256: `1c86e2a97f9f050cc7fb89a2f210a6d961d4466a982afe70cd6c7773020d6b9b`.

# Decisions for e4cb0224ca42

## D1 — Treat the prior audit as a lead, not proof

- **Original rationale:** unknown; the retained audit reported silent underfill against the same baseline hash.
- **Alternatives:** accept the audit text; dismiss it as historical; independently reproduce.
- **Choice:** independently load the immutable baseline and reproduce easy seed 3/sample 0 with `n_rects=2`.
- **Probe/evidence:** `repo/generators/e4cb0224ca42/counterexamples/silent-underfill-seed-3.json` records baseline and repaired grids and hashes.
- **Failure mode/limit:** this one witness establishes count drift, not the prevalence by itself; the retained prior audit supplies the 0..255 baseline census and the new regression supplies a repaired 2,304-case sweep.

## D2 — Replace bounded rejection with constructive exact placement

- **Original choice:** sample shapes and positions, retry a bounded number of times, silently continue when no placement succeeds.
- **Alternatives:** increase retries; reject/resample the whole example; construct a feasible packing.
- **Choice:** construct exact placements. Public override cases use four separated slots; defaults use proven canonical-profile templates.
- **Why:** increasing retries preserves a nonzero silent-failure path. Whole-example rejection is honest but complicates deterministic sample indexing. Construction makes count exact and cheap.
- **Probe:** seed-3 regression plus the 2,304-case band/count/seed sweep.
- **Limit:** override slots cap individual rectangle size according to the selected region; size is not a public axis and remains within the documented {3,5,7} domain.

## D3 — Permit diagonal contact, prohibit cardinal contact

- **Original choice:** require a full one-cell moat including diagonals.
- **Alternatives:** retain moat and reject canonical train 0; accept all contact; use 4-connectivity/cardinal separation.
- **Choice:** 4-connected objects may touch at corners but not by an edge.
- **Why/evidence:** canonical train 0 has diagonal corner contact and must pass. Cardinal contact would make different-color rectangles geometrically tangent and weakens object separation.
- **Test:** every canonical input passes; a targeted cardinal-touch impostor fails.

## D4 — Shrink the advertised axis contract

- **Original choice:** nine axes, including aliases, fixed single-token values, dead texture degenerates, and multiple counts that did not independently control output.
- **Alternatives:** implement every old axis; mark most diagnostic; expose only recoverable controls.
- **Choice:** `grid_h`, `grid_w`, `n_rects` only.
- **Why:** these are exact, independently observable, and useful. Shape variety, colors, reflection, and template profile remain internal distribution choices.
- **Probe:** strict override matrix and `observe_overrides` equality.
- **Limit:** callers cannot request a specific rectangle dimension or palette through the public contract.

## D5 — Use a four-profile default teaching schedule

- **Original choice:** independent random draws could yield one-object or all-square lessons by chance.
- **Alternatives:** rely on a large random census; rejection-sample complete lessons; schedule canonical-profile pairs.
- **Choice:** recurring 7x9, 9x11, 8x10, and 9x11 templates, always with two objects; three of four profiles include a non-square object.
- **Why:** any three demonstrations from the four-pair window refute center-only, one-axis-only, squares-only, and first-object-only rivals, including every held-out query rotation.
- **Probe:** `test_declared_four_pair_schedule_survives_every_query_rotation` exhausts all four starts/queries in all bands.
- **Limit:** the finite rival set does not prove universal identifiability; templates deliberately stay close to canonical morphology.

## D6 — Keep difficulty observable through a lawful palette bijection

- **Initial v4 choice:** difficulty was validated but did not affect any draw; defect lint flagged byte-identical bands.
- **Alternatives:** change object count or size by band; remove difficulty; rotate colors.
- **Choice:** apply distinct color-cycle offsets for easy/medium/hard, preserving distinctness and geometry.
- **Why:** it makes the parameter observable without starving any band of canonical-profile support or changing lesson logic.
- **Probe:** same seed/sample produces three distinct lawful grids; defect lint is green.
- **Limit:** “difficulty” is distributional metadata here, not a calibrated reasoning-complexity score.

## D7 — Add executable semantic rivals and witnesses

- **Alternatives:** prose counter-hypotheses only; witnesses without rival claims; direct rival scoring.
- **Choice:** direct rival functions, witness-to-rival mappings, canonical shortcuts, and a `lesson_identifiable` hook that requires every declared rival to be refuted by at least one demonstration.
- **Why:** labels can be correct while a lesson teaches a shortcut. Executable rivals make the claim falsifiable.
- **Probe:** strict semantic gate and task-local witness tests.
- **Limit:** undeclared rivals remain untested.

## D8 — Omit the formal schedule-period opt-in while testing the period locally

- **Prior v4 choice:** declare `LESSON_SCHEDULE_PERIOD=4`.
- **Observed failure:** strict semantic stage returned WARN solely because the period was not separately enumerated, despite 600/600 strict inputs, verified witnesses, 12/12 identifiable lessons, and 0/48 ambiguous rotations.
- **Alternatives:** accept a red after battery; run a separate census that the battery cannot consume; omit the opt-in and retain exhaustive local coverage.
- **Choice:** omit the formal constant, keep `SCHEDULE_PROFILES`, and exhaust all four starts/query positions in portable tests and the larger rotation census.
- **Limit:** generic tooling reports sampled profile coverage rather than a formally enumerated period receipt. Shared-tool feedback F2 proposes a one-command remedy.

## D9 — Leave the Racket authority unchanged

- **Choice:** no rule edit.
- **Why:** canonical outputs, rule smoke, Python mirror, and generated inputs agree; the defect was entirely in input generation and validation.
- **Failure mode checked:** a generator repair that silently broadens outside the authority. The strict manifold remains solid odd rectangles only.

## D10 — Require arbitrary held-out query positions and widen the lesson census

- **Choice:** treat three ordered demonstrations plus one query as the production lesson, and require identifiability when any of the four pairs is held out.
- **Why:** an ordered window can accidentally teach by position; a production-only pass is insufficient for this schedule.
- **Evidence:** `checks/lesson-census-final.json` materialized 300 lessons (100 per band), 1,200 source-bound pairs, and 1,200 query rotations. Production and rotation statuses are both `no_ambiguity_found`, with zero materialization, hook, or scoring errors.
- **Limit:** the census samples seeds and tests declared/searched rivals; it does not enumerate all seeds or all conceivable hypotheses. The task-local test separately exhausts all four schedule starts and query positions in every band.

## D11 — Retain the canonical-profile restriction explicitly

- **Self-review question:** did the constructive repair merely exchange silent underfill for a narrower, shortcut-prone distribution?
- **Finding:** exact counts are covered over 2,304 override draws and query order is exhaustively checked, so neither failure remained. Default lessons nevertheless intentionally use two distinct-color, canonical-like objects.
- **Choice:** keep that restriction visible rather than claim unsupported repeated-color segmentation or uniform 1–3 object production. One- and three-object behavior remains exact through public overrides.
