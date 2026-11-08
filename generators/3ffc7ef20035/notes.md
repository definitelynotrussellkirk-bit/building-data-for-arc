# Current account: 3ffc7ef20035

## Intended rule and authority

The input contains one sparse blue (`1`) object and one separate non-blue
distractor on a zero background. The output fills the tight axis-aligned
bounding rectangle of **all** blue cells with cyan (`8`) and preserves every
cell outside that rectangle. The canonical Racket authority and `RULE_HASH`
`bde384898938` were not changed in this review.

Final generator version: **3.2.1**. Final `generator.py` SHA-256:
`ceaa3266672c82d950423e55b28edc9e156d5e3da0a4b4b3d593bb34cd74b213`.

## Reproduced baseline teaching defect

The 3.0.0 source had six hand-picked normalized blue shapes and only one
profile whose blue object needed 8-connectivity. A deterministic cyclic lesson
starting at index 4 placed three 4-connected shapes in the demonstrations and
the diagonal-only shape in the query. The rival “fill only the first
4-connected blue component's bbox” therefore fit every demonstration and
changed the query. The exact baseline lesson is retained at
`counterexamples/first-4-connected-lesson-window.json`.

The ordinary before battery was 12/12 green, but the source-bound 100-lessons
per band census found 48/300 production lessons and 198/1,200 query rotations
ambiguous against the declared rivals (`checks/lesson-census-before.json`).

A second, stronger rival was identified from the canonical data: fill the bbox
only when the normalized blue shape is one of the four distinct canonical
geometries; otherwise recolor only the blue cells. It fits all five canonical
pairs. An exact lawful off-canonical counterexample is retained at
`counterexamples/canonical-shape-whitelist.json`.

## Repair decisions

- Expanded the profile family from 6 to 10 explicit, observable shapes.
- Alternated five 4-connected and five diagonal-only 8-connected profiles.
- Interleaved the four canonical geometries with six off-canonical geometries.
  Every cyclic four-pair lesson has two diagonal witnesses and at least two
  off-canonical witnesses, so holding out any query leaves at least one of each
  in the three demonstrations.
- Declared `LESSON_SCHEDULE_PERIOD = 10` for exhaustive start-residue checks.
- Added `first_4_connected_blue_component` and
  `canonical_shape_whitelist` to the executable semantic rival contract, with
  corresponding witnesses.
- Reversed the intermediate choice that called several merely plausible rivals
  “canonical shortcuts.” `CANONICAL_SHORTCUTS` now contains only the shape
  whitelist, because every member of that map must actually fit every canonical
  pair. The broader rivals remain in `LESSON_COMPETITORS`.
- Made `lesson_identifiable` query-aware: a rival is blocking only when it fits
  all demonstrations **and** predicts a different answer for the actual query.
- Made task tests portable with `reviewer_support.find_root`, `canonical_path`,
  and `canonical_pairs`, and added regressions for canonical fit, rival coverage,
  every cyclic start, exact overrides, source binding, and RNG purity.

## Final evidence

- Full compact after battery: 12/12 stages green at the final source hash,
  `checks/after-final-v2/`.
- Focused task tests: 22 passed,
  `checks/task-tests-final-v2/`.
- Required query-rotation semantic gate: passed,
  `checks/required-rotations-v2/`.
- Production census: 300 lessons, 1,200 pairs, 0 ambiguous lessons and
  0/1,200 ambiguous rotations, `checks/lesson-census-after-v2.json`.
- Declared-period census at seed 0: all 30 starts across three bands and all
  120 query rotations passed, `checks/schedule-census-after-v2.json`.
- Final visible-only solve: 3/3 demonstrations passed in one revision, with
  earlier rule exposure declared and no reference consultation during the
  solve, `solve/summary.json`.

## Known limits

The profile family is still a finite, orientation-specific ten-shape grammar;
there are no D4 shape transforms or arbitrary 8-connected polyominoes. The
censuses establish support only against the six declared executable rivals,
not uniqueness against every conceivable program. The declared-period result
exhausts start residues at seed 0 across the three difficulty bands; the larger
random census covers 100 lessons per band but is not an exhaustive seed proof.
No remaining blocking defect was found within this stated scope.
## Current reviewer considerations

Source SHA-256: `ceaa3266672c82d950423e55b28edc9e156d5e3da0a4b4b3d593bb34cd74b213`.

# Decisions for 3ffc7ef20035

Final generator version: 3.2.1
Final generator SHA-256: `ceaa3266672c82d950423e55b28edc9e156d5e3da0a4b4b3d593bb34cd74b213`

## D1 — Preserve the authoritative transformation

**Choice.** Keep the canonical rule and `RULE_HASH` unchanged: fill the tight
bbox of all blue cells with `8`, preserving the distractor and exterior.

**Why.** Canonical pairs, the Python mirror, and Racket authority already agree.
The defect was in sampling and lesson assembly, not labels. Changing the rule
would have hidden the curriculum problem and exceeded the assigned scope.

**Evidence.** `checks/after-final-v2/checks/3ffc7ef20035_after_rule_smoke.log`
and `..._authority_sync.json`.

## D2 — Treat lesson identifiability, not isolated grid validity, as the defect

**Prior choice.** Version 3.0.0 supplied six individually lawful profiles. Its
small battery was green.

**New choice.** Evaluate consecutive three-demo-plus-one-query lessons against
executable rivals. The retained start-4 lesson proves that correct isolated
labels can still form an ambiguous lesson.

**Probe.** `counterexamples/first-4-connected-lesson-window.json` records seed
911, hard band, the three demonstrations, diagonal query, intended outputs, and
rival outputs. The failing regression was observed before the repair in
`checks/tdd-red/`.

**Failure mode avoided.** A solver can learn “operate on the first 4-connected
blue component” from all demos and fail only on the query.

## D3 — Use a ten-profile deterministic schedule

**Choice.** Expand to ten explicit profiles and alternate connectivity class:
4-connected, diagonal-only, 4-connected, diagonal-only, and so on. Interleave
canonical-status as `C,N,C,N,N,C,N,C,N,N`.

**Why this ordering.** A lesson has three demonstrations and one query. Every
cyclic window of four therefore contains exactly two diagonal-only profiles and
at least two off-canonical profiles. Under any query rotation, at least one
connectivity witness and one shape-family witness remain demonstrations.

**Alternatives rejected.**

- *Randomly sample shapes.* Broader marginal diversity does not guarantee a
  witness in each assembled lesson.
- *Move the one old diagonal shape earlier.* This fixes one start but leaves
  other cyclic starts and rotations vulnerable.
- *Reject diagonal queries.* That narrows the domain instead of teaching it.
- *Require every single grid to refute every rival.* Some valid canonical-shaped
  grids necessarily agree with the canonical whitelist rival; identifiability
  is a lesson-level property.

**Evidence.** `checks/schedule-census-after-v2.json` exhausts all ten start
residues at seed 0 in easy/medium/hard, with 0/30 production ambiguities and
0/120 rotated ambiguities.

## D4 — Model the strongest canonical-fitting rival explicitly

**Choice.** Add `canonical_shape_whitelist`: apply the intended bbox fill for the
four distinct normalized blue shapes in the five canonical pairs; on any other
shape, recolor blue cells only.

**Why.** This is a stronger shortcut than a fixed bbox size or corner template:
it fits every canonical label exactly while refusing geometric generalization.

**Contract correction.** An intermediate implementation listed four other
plausible rivals under `CANONICAL_SHORTCUTS`, although they did not fit every
canonical pair. A failing test exposed the mismatch
(`checks/tdd-red-canonical-contract/`). The final map contains only the genuine
canonical-fitting whitelist; all six rivals remain in `LESSON_COMPETITORS`.

**Evidence.** `checks/question-generator-shortcuts/counterexample-v2.json` and
the portable canonical-fit test in
`generators/3ffc7ef20035/tests/test_generator_3ffc7ef20035.py`.

## D5 — Make identifiability query-aware

**Choice.** Report a competitor only when it fits all demonstrations and changes
the actual query answer.

**Why.** A rival that survives the demonstrations but happens to agree on the
query is not a prediction ambiguity for that lesson. This definition also makes
query-rotation checks meaningful and avoids rejecting harmless equivalence on a
particular instance.

**Limit.** Passing a finite named-rival set is not a proof of unique induction.

## D6 — Keep controls explicit and observable

**Choice.** Preserve the existing grid-size, distractor-size, distractor-color,
and shape-profile controls. Each of the ten shape overrides maps to one exact
recoverable normalized geometry; no retries or silent coercion were introduced.

**Why.** The repair needed curriculum coverage, not uncontrolled random growth.
Explicit profiles make exact cyclic reasoning, override validation, and replay
possible.

**Evidence.** Full battery override stage and 22 focused tests.

## D7 — Portable focused tests are part of the repair

**Choice.** Replace fixed parent-depth canonical paths with
`reviewer_support.find_root`, `canonical_path`, and `canonical_pairs`. Add tests
that bind the canonical rival, schedule period, every cyclic window, source hash,
validator impostors, overrides, determinism, and RNG purity.

**Why.** The return must replay in a fresh packet extraction; source-depth
assumptions break there. The tests also prevent a future profile reorder from
silently recreating the lesson defect.

## D8 — Scope and remaining limitations

The final random census covered 100 lessons per band (300 total), all 1,200
materialized pairs, and all 1,200 query rotations with no declared-rival
ambiguity. The fixed-seed period census covered every declared start residue.
The remaining restriction is the finite ten-shape orientation-specific grammar;
arbitrary polyomino and orientation generalization remain untested rather than
claimed.

## 2026-10-24 native parametric admission build

The production generator and canonical Racket rule remain unchanged. A task-local
native adapter now exposes two episode-fixed settings:

- `all_blue_bbox`: the exact canonical program, byte-for-byte.
- `bar_orientation_component`: detect the unique non-blue selector bar,
  classify it as horizontal or vertical, use that result to select blue object
  0 or 1 in row-major order, then fill the selected object's tight bbox cyan.

The alternate setting has a real sequential dependency. Step A returns the
selected object index; Step B cannot determine the painted rectangle before it
receives that index. The protected-Racket wrong-intermediate replay changes 34
final cells (`checks/3ffc7ef20035/causal/witness.json`).

The adapter supports 2–6 demonstrations and four independently stored queries;
the public projection reveals one query per turn with no settings, program,
answer, future-input, seed, or total-query hint. Same-seed inputs match across
settings. Every four-query episode includes a substantive 30×30 case.

A TDD regression caught one sampler defect: ordinary dimensions were chosen
without transformed shape extents, allowing two intended blue objects to touch
diagonally under required 8-connectivity. Dimensioning now includes both shape
extents and preserves a multi-cell separation. Final task-local suite: 50/50.

Bounded self-audit: 30 episodes over settings, seeds 0/17/991, and demo counts
2..6; 240 mirror label claims; 15 matched-input requests; 17 hypotheses per
episode; eight public files; no tested survivor or leakage finding. Native
qualification passed four jobs (two settings × two seeds), 40 protected-Racket
evaluations, and 30×30 stress queries. Evidence is under
`workspace/parametric/evidence/`, `checks/3ffc7ef20035/qualification/`, and
`checks/3ffc7ef20035/causal/` in the return packet.

Reviewer status is **ready**, not accepted. The owner must integrate these exact
bytes, rerun native qualification, replay the causal witness, and perform fresh
native acceptance before the variant is usable or training-admitted.

<!-- arcpuzzles-trainer-ambiguity:start -->
## Current trainer ambiguity follow-up

Claude supplied 1 exact canonical lesson(s) with a proposed alternative rule. Retained privately with source hashes and all stored queries: `evidence/trainer-ambiguity-current/current.json`. These are **open describer flags**, not confirmed wrong labels or failed current parametric qualifications. Check whether the proposed rival fits every demonstration and changes any stored query; distinguish source revisions before repairing. Approval and training state are unchanged.
<!-- arcpuzzles-trainer-ambiguity:end -->
