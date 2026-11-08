# Working notes: 9e7fcd5605d8

## Current parametric extension: enclosed-region threshold

A separate native adapter under `workspace/parametric/` adds `min_holes=2` while
retaining the exact canonical program for `min_holes=1`. The production generator,
canonical source and approval hashes remain unchanged. Region count is computed
from 4-connected bbox-complement regions after excluding the rim; enclosed area
is not a substitute. The input-dependent count selects the whole-object color.

Constructive two-demo teaching contrasts cover open/closed, area/count, diagonal
connectivity, exact/at-least and exterior-region shortcuts. Counts are independently
2–6 demos and 1–4 queries; default is 3+4. Settings use identical input streams and
stable prefixes. Four queries include 11×11, 18×24, 24×21 and substantive 30×30 scenes.
`workspace/parametric/verify.py` is the reusable protected-Racket label/rival and
first-query-public-projection verifier. Its current evidence and native manifest
are under `workspace/parametric/evidence/`; native qualification and the causal
wrong-intermediate witness accompany this return under `checks/9e7fcd5605d8/`.

Owner action after intake: run native qualification and acceptance on the exact
integrated source. Reviewer readiness does not grant acceptance or training
admission. Retained canonical audit statuses are unchanged. Claims cover a finite
rival set and separated-object grammar; foreground-connectivity alternatives that
agree on that grammar and universal induction remain outside the evidence.

## Lead used

I used retained return `review-590099c9bdb33930:v0001` only as a lead. Its source hash matched the selected baseline (`1d6418ec...`), and it supplied the open-U counterexample. I independently reproduced the current-source behavior and ran the immutable before battery before repairing anything.

## Baseline diagnosis

The selected v1.3.0 generator conflated two different predicates:

- canonical authority: a same-color component contains an enclosed 4-connected background region inside its bounding box;
- generated shortcut: the component does not completely fill its bounding box.

A 3x3 open U has a non-full bounding box but no enclosed region, because the missing cells reach the bounding-box boundary. The baseline distribution emitted only filled rectangles and closed outlines, so the shortcut fit both the canonical demonstrations and ordinary generated lessons.

The completed before battery reported 7 green, 2 advisory, and 3 failed stages. Blocking failures were a missing `RULE_HASH`, dead/overlapping texture declarations, and a non-falsifiable override API that accepted unknown keys and failed many exact-control requests. Rule smoke and authority synchronization were already green, so changing the Racket authority was not justified.

## Repair

Version 2.0.0 replaces rectangle-only sampling with a constructive four-slot topology curriculum. Each input contains 2--4 separated components, at least one truly hole-containing component, and at least one hole-free open concavity. Optional multi-hole components, one or two input colors, canonical-size anchors, and broader size/count profiles add variation without weakening the contrast.

The public control surface now contains only six exact observable axes: grid height, grid width, hole-containing count, hole-free count, multi-hole count, and distinct input-color count. Unknown, out-of-range, and wrong-type overrides are rejected. Every legal boundary combination is constructible.

The generator now pins the unchanged canonical rule hash `02bf16fb38e9`, contains an input-pure Python mirror, declares the canonical-fitting `bbox_nonfull_is_hole` shortcut as a semantic rival, and provides an executable open-concavity witness plus lesson-level identifiability hook.

## Evidence

- Completed before battery: `checks/before-rerun/` -- 7 green, 2 advisory, 3 failed.
- Completed final after battery: `checks/after/` -- all 12 stages green.
- Selected task tests: 146 passed in the portable task-test runtime.
- Source-bound lesson census: 100 lessons per band, 300/300 materialized, 1,500/1,500 exact inputs unique, zero ambiguous lessons, and every declared rival refuted in every lesson.
- Task-local cyclic-query probe: 100 five-pair windows per band, all 1,500 query rotations identifiable, with the rival refuted in all 1,500 rotation checks.
- Exposed post-repair solve: first genuine revision passed all 4 visible demonstrations; masked-query correctness was withheld.

## Limits

The supported generator domain is intentionally bounded to 10--16 rows, 10--18 columns, 2--4 components, one or two hole-containing components, one or two hole-free components, at most one multi-hole component, and one or two input colors. Finite declared-rival checks do not prove universal induction or exclude every possible shortcut. The Python mirror is corroborative; the selected Racket rule remains authoritative.

An initial repository-wide pytest run stalled after entering `tests/test_archival_reference.py::test_canonical_approval_never_transfers_to_archival_execution`. The isolated test passed in 3.16 seconds, the other 272 tests passed with it deselected, and a fresh final unfiltered run passed all 273 tests in 266.90 seconds; the transient diagnostic logs are retained.
## Current reviewer considerations

Source SHA-256: `cd98620036c5eafc90972da4cbcbd959826f58ddcddbfd3b2166a21df424706d`.

# Decisions for `9e7fcd5605d8`

## 1. Preserve the Racket authority

**Choice.** Keep the selected canonical rule unchanged and pin `RULE_HASH = "02bf16fb38e9"`.

**Rationale.** Baseline rule smoke and authority synchronization passed, and the retained counterexample exposed a generator-distribution error rather than an authority error.

**Alternative rejected.** Rewriting the Racket rule to match “non-full bounding box” would have changed correct topology semantics merely to preserve a shortcut.

**Probe / failure mode.** Final rule smoke and authority-sync are green; the Python mirror matches all canonical pairs. The archival rule remains divergent, as it was before, but the selected authority has execution parity.

## 2. Teach enclosed topology, not rectangular appearance

**Choice.** Every ordinary input includes a hole-free open concavity, plus at least one component with an actual enclosed background region.

**Rationale.** A U/C/L-like component is the minimum contrast separating the canonical predicate from the canonical-fitting shortcut “non-full bounding box means hole.” Requiring the contrast in every input prevents a four-example lesson from accidentally omitting it.

**Alternatives rejected.** Filled rectangles plus closed rectangular outlines reproduce the baseline shortcut. Unconstrained random polyominoes add rejection complexity and can obscure whether a missing cell is truly enclosed.

**Probe / failure mode.** The open-U regression test makes the authority return 4 and the rival return 8. Generated-input tests check this disagreement across all bands. Remaining limitation: only one declared canonical-fitting topology rival is scored.

## 3. Use constructive separated slots

**Choice.** Place 2--4 independently transformed templates in four quadrants separated by a full background row and column.

**Rationale.** This guarantees component separation, makes all count combinations constructive, and avoids rejection-sampling tails.

**Alternatives rejected.** Free placement with overlap rejection can silently collapse components or make legal joint overrides seed-dependent.

**Probe / failure mode.** All 64 boundary combinations of the six exact axes pass `self_check` and reproduce the requested observations. Domain limit: no more than four components.

## 4. Include single-hole, multi-hole, open-concave, and filled components

**Choice.** Hole-containing components use one-hole templates, with an optional two-hole template; hole-free components always include an open concavity and may include a filled rectangle.

**Rationale.** Multi-hole examples show that classification is existential rather than “exactly one hole,” while filled components retain canonical-like negatives.

**Alternative rejected.** Exposing hole count as the output would teach a different task; the output remains binary 8-versus-4.

**Probe / failure mode.** Independent component analysis counts 0, 1, and 2 holes in fixed regressions, and exact `n_multi_hole` overrides are observable.

## 5. Bound the palette to one or two non-output colors

**Choice.** Use one or two colors from `{1,2,3,5,6,7,9}`, assigning colors across components while excluding output labels 4 and 8.

**Rationale.** One color preserves canonical support; two colors prevents a learner from treating all nonzero cells as one object. Excluding 4 and 8 prevents input/output-label ambiguity.

**Alternatives rejected.** Three or more colors add little semantic value with at most four components. Keeping the baseline dead palette controls would make the API untruthful.

**Probe / failure mode.** Exact color-count observations pass at both boundaries and canonical-like profiles require one shared color.

## 6. Schedule canonical anchors and broad profiles

**Choice.** Rotate four profiles by `sample_index mod 4`: two canonical-size/count anchors, a two-color broad case, and a two-color multi-hole case.

**Rationale.** Each four-example lesson receives canonical support and broader contrasts without relying on random luck. Canonical dimensions are 10x10, 10x11, or 11x11; broad dimensions vary by difficulty within the declared domain.

**Alternative rejected.** Purely random profile sampling can miss canonical support in a 20-draw band check and can produce semantically homogeneous lessons.

**Probe / failure mode.** Profile-floor passes in every band. Every four-demo window and every cyclic holdout of a five-pair window refutes all declared competitors. The schedule is deterministic and therefore intentionally not an IID profile draw.

## 7. Replace decorative axes with six exact controls

**Choice.** Publish only `grid_h`, `grid_w`, `n_hollow`, `n_hole_free`, `n_multi_hole`, and `n_distinct_colors`; reject unknown keys and invalid types/ranges.

**Rationale.** Each control can be recovered exactly from pixels, making the override contract falsifiable.

**Alternatives rejected.** `texture`, `palette_kind`, `palette_size`, and similar aliases were dead, overlapping, or semantically vague in the baseline.

**Probe / failure mode.** The final override stage is green with zero findings or warnings and an explicit unknown-key rejection verdict.

## 8. Add an independent mirror and reusable curriculum probe

**Choice.** Implement a Python flood-fill mirror, a declared shortcut, a witness, and `workspace/lesson_probe.py` for all query rotations.

**Rationale.** The mirror enables fast property tests; the rival/witness contract makes the teaching goal executable; the probe fills the shared census limitation that only one query position is materialized.

**Alternative rejected.** A prose-only rule description cannot detect semantic drift or a lesson where the distinguishing pair is held out as the query.

**Probe / failure mode.** Source-bound Racket census: 300/300 lessons, 1,500 unique inputs, zero ambiguity. Task-local cyclic probe: 1,500/1,500 rotations pass. These are finite declared-rival checks, not a proof against undeclared shortcuts.
