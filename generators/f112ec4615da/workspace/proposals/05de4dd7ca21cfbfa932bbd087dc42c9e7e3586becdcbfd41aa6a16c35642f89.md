Task `f112ec4615da`: generator `3.0.0` → `4.0.0`; final SHA `6c231b14fb87bf876361232ba1952d15e73c992f373a0119f638876e5ed4da13`.
Defect: invalid scalar calls were accepted, no semantic lesson contract existed, and `global_min_else_max` fit all 7 canonical pairs.
Repair: strict call validation, safe palette-role scheduling, executable branch/rival witnesses, and a three-demo lesson-identifiability hook.
Canonical Racket authority and `RULE_HASH=8724ec70a45a` were not changed.
After battery: 11/12 green; every generator-owned stage passes, including strict defect lint, profile floor, overrides, and semantic gate.
Semantic evidence: 600/600 strict draws, six witnesses, 60/60 rival claims, 12/12 lessons, and 0/48 ambiguous smoke-test rotations.
Large census: three demos + one query; 300/300 production lessons and 1,200/1,200 query rotations had no declared-rival ambiguity; 1,199 unique inputs.
Task tests: 7 new portable tests pass separately; aggregate task-tests remain blocked before pytest by the frozen fixed-root fixture.
Prototype: proposed episode-level `overlay_priority` variant; two settings, exact Racket for both, every retained demo/query distinguishes them.
Remaining blocker: execution-equivalent active authorities differ only in exact text; fixing shared selected `target_code` is outside task scope.
Blind and exposed solves each passed all 3 visible examples on revision 1; masked query correctness remains unknown by policy.
Acceptance: needs attention — repair is verified, but authority formatting and inherited fixture migration are maintainer-owned blockers.

# Detailed review

## Baseline and root cause

The unchanged before battery on generator SHA
`438a4a576a6a5790a9f92dc00bba8835fe27f264c13cbfcb6a2ad2ad6fd68cc1`
finished with 9 green stages, one advisory semantic stage, and two failures:
strict defect lint and authority sync. The semantic stage had no declared
contract. The retained audit `review-1f4b2a09912ae523:v0001` supplied the
color-ranking hypothesis and fixed-root fixture as leads; both were reproduced
against the pinned baseline rather than accepted as current measurements.

The strongest rival, `global_min_else_max`, chooses the globally smallest
foreground color when locally present and otherwise the local maximum. It fits
all seven canonical labels because their color ranks happen to align with the
positional priority. A direct final-source counterexample and Racket output are
retained in `checks/shortcut/comparison.json` and answered fully in
`QUESTION_ANSWER.md`.

## Implemented repair

`generator.py` now:

- enforces plain integer seed and nonnegative sample index plus the existing
  difficulty and exact-dimension contracts;
- maps four sampled colors to TL/TR/BL/BR through 21 safe role-rank
  permutations, so every generated input refutes the numeric-color rival;
- declares strict-domain, five branch, and rival-refutation witnesses;
- declares the rival consistently for canonical-shortcut, semantic, and lesson
  checks; and
- verifies three-demo/one-query lesson labels and rival identifiability.

No canonical masks, dimensions, densities, profile prior, spatial roles, or
Racket rule changed. Focused source diff is transported in the return patch.

## Verification

### Full and focused checks

- Before battery: `checks/before/` — 9 green, 1 advisory, 2 failed.
- Final after battery/resume: `checks/after/` — 11 green, 1 failed.
- Standalone strict semantic gate: `checks/semantic-after/` — PASS.
- Standalone strict defect lint: `checks/defect-lint-after/` — PASS.
- Profile floor: 17/60 exact/envelope hits; easy 6/20, medium 4/20,
  hard 7/20; no crashes or warnings.
- New task-local tests: `checks/task-local/test_review_contract.log` (4 passed)
  and `test_parametric_priority.log` (3 passed, including live Racket).
- Portable aggregate task tests: `checks/task-tests/result.json` — exit 2 before
  pytest because the frozen fixture resolves a nonexistent canonical path.

The completed after battery's sole failure is exact-text `authority_sync`.
Canonical `program_solution` and selected `target_code` have different exact
SHA-256 values but one whitespace/comment-normalized rule hash; both execute
correctly on all six training and one test pair. The gate itself reports
execution parity PASS. This task's permitted patch scope cannot change the
selected shared base record.

### Lesson evidence

The strict semantic gate measured 600 draws (200 per band): strict acceptance
600/600, all six witnesses present, declared rival disagreement 60/60 checked
cases, 12/12 three-demo lessons identifiable, and 0/48 ambiguous query
rotations. See
`checks/semantic-after/checks/f112ec4615da_after_semantic_gate.json`.

The production-shaped census used three demonstrations, one query, 100 lessons
per band, and held out each of four pairs as query. It materialized 300/300
lessons, checked 1,200 rotations, found zero hook/scoring/materialization errors
and zero ambiguities, and recorded 1,199 exact unique inputs. See
`checks/lesson-census.summary.json` and the full source-bound
`checks/lesson-census.json`. This is bounded evidence against declared rivals,
not universal identifiability.

## Parametric-rule assessment

A suitable small parameter exists: the high-to-low overlay priority. The
prototype preserves the original four aligned roles and local selection
operation while varying only precedence:

- `tr_bl_br_tl` is the canonical/default setting;
- `tl_br_bl_tr` is the alternative.

`workspace/parametric/prototype.py` chooses one setting once per episode and
emits two demonstrations plus one query. Every pair deliberately distinguishes
settings. Exact Racket programs are retained under `workspace/parametric/rules/`;
their SHA-256 values are
`0c0635d315a15f93955a6cb01f27f7ce50642709608fc735892de1adafb0152e`
and
`9254a7ef603f91a93d83268afab9226bf28be626cd9998201defdad459f169af`.
All six retained pair executions match Python, every demo refutes the alternative,
and each query also differs. Evidence:
`checks/parametric/overlay-priority-seed19.json`. Status: **proposed prototype**,
not production-approved.

## Solve records

The required blind task `410fb6b72f16` was solved before opening generator
sources. Revision 1 recolors orthogonally isolated 1-cells to 2 and passed 3/3
visible examples; earlier exposure and reference consultation were both `no`.

The post-repair solve was prepared from final generator SHA `6c231b14…`. With
honest earlier rule exposure `yes` and reference consultation `no`, revision 1
implemented TR > BL > BR > TL and passed 3/3 visible examples. Both solve
records remain visible-feedback-only; private query labels were not exposed.

## Audits

Two findings-only audits were completed without modifying their targets. See
`AUDIT.md` and `checks/audit/`:

- `cf0dd146ab42`: an arbitrary six-code transform map is not teachable from the
  sampled three demonstrations; a Racket-backed ambiguous lesson is retained.
- `0bd65c18b34c`: generated ties never distinguish row-major-leftmost from a
  topmost/rightmost rival; a Racket-backed exact geometry probe is retained.

## Completion status

The selected generator repair and required audits are complete, but aggregate
acceptance remains **blocked** by two inherited/out-of-scope failures: the
frozen fixture's portable path and the active-authority exact-text mismatch.
Neither was bypassed or weakened.
