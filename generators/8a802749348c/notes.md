# Working notes: 8a802749348c

Record design decisions, hypotheses, review findings, and unresolved questions here.
Imported associated notes retain original evidence/timestamps in `evidence/associated_notes.jsonl`.

## 2026-10-26 portable task-test repair

The prior audit identified a portable-runtime test-harness defect rather than a generator defect. The task test now resolves canonical data through `reviewer_support.find_root` / `canonical_path` with a staged-data fallback, and uses `puzzle_generators.rule_wrap` instead of the unavailable legacy `scripts.rule_smoke` import. The generator and selected canonical Racket source remain byte-identical. The repaired portable suite executes the canonical hash, six-pair parity, and protected-Racket A-B-A checks; all 22 task tests pass in `checks/8a802749348c-tests/result.json`.

The owner-managed audit disposition index is intentionally unchanged; this reviewer return records the repair and fresh execution evidence without asserting owner acceptance or closing the prior audit on the owner's behalf.

## 2026-10-26 parametric build decision

The ordinary generator and exact selected canonical Racket source remain unchanged. The new episode-fixed parameter is `postprocess`: `none` preserves the canonical L-ray rule byte-for-byte; `mark_crossings` first produces the canonical ray grid, then marks each input-empty same-color diagonal crossing and its four orthogonal neighbors with color 9. Inputs are matched across settings, support 2–6 demonstrations and 1–4 queries, and include a substantive 30×30 query.

A protected counterfactual that skips the ray stage changes the selected final output, because the crossing predicate reads cells created only by those rays. The authoring preflight passed both settings at seeds 0 and 17 (32 protected-Racket evaluations), the causal witness replayed, and the 16 one-query public projections verified. These are reviewer authoring results only; owner source review, native qualification/acceptance, and any training admission remain pending.


## 2026-10-26 adversarial round 2

A minimum-two-demo adversarial scan found that some seeds allowed a fixed
near-center plus marker to fit every demonstration even though the intended rule
is to derive the crossing from the ray intermediate. A regression test now scans
all nine offsets around the geometric center across 128 seeds. It failed on the
old sampler, then passed after demo crossing centers were changed to a
seed-shuffled no-replacement schedule.

Fresh evidence records 23 passing task tests, a 128-seed matched-input sweep that
observed all nine offsets, 72 additional protected-Racket parity evaluations,
four authoring-preflight jobs with 32 protected-Racket evaluations, causal-witness
replay, 16 public projections, and first-turn invariance checks. Scope remains
finite; owner acceptance and training admission remain pending.
