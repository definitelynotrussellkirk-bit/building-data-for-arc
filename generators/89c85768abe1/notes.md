## Current native parametric proposal

`workspace/parametric/adapter.py` adds episode-fixed `mode=all|largest_component`.
The exact canonical default, selected `generator.py` version 2.1.0 and authority
hash `d273f364d771` are unchanged. The alternate completes all colored rectangles,
then retains the largest four-neighbor foreground component, preserving its colors.
Completion can create multicolor adjacency that the sparse corner input lacks.

Two constructive demonstrations teach total occupied area, connectivity, and
selection after completion. Self-review strengthened the first area comparison
to a one-cell margin, defeating newly-painted-area ranking, and separated the
second example under eight-neighbor connectivity. Four-box scenes vary between
two and three components. Strict output typing rejects Boolean color aliases.

The API supports 2–6 demonstrations and 1–4 queries; normal use is 3/4. All modes
share input streams. Four queries include 30x30 geometry. Ties have deterministic
row-major semantics but are excluded from sampled queries. Finite teaching checks
cover 16 declared rules, not arbitrary rule uniqueness. Current bounded sampler
review: `checks/89c85768abe1/adversarial/report.json`; protected labels and native
qualification are supplied in the return's `checks/89c85768abe1/qualification/`.

The task-local `export.py` writes verified batches and one-query visible turns;
its verifier replays Racket labels and rejects private/future-query leaks and
rehashed corruption. See its adjacent README for runnable commands and limits.
Native exact-source owner qualification and acceptance remain the next action.
This proposal does not change production size overrides or training admission.

# Working notes: 89c85768abe1

## 2026-10-04 repair

Prior lead used: `review-6c4f2053a7aa3c1b:v0001`, source SHA-256
`78d36bf63a4d03d39a68b373ca1201df5974851dc6685a2911c529650e08eb8a`.
Its ignored-control, degenerate-bypass, and overlap-validator findings were
reproduced by the assignment's before battery; the prior claims were not treated
as measurements of the selected baseline.

The root cause was an over-advertised nine-axis API wrapped around a narrower
three-quantity construction. Several labels were never read, difficulty bands
silently narrowed advertised integer domains, degenerate early returns bypassed
shape controls, and `self_check` only counted colors. Version 2.0.0 replaces that
surface with three exact pixel-observable axes (`grid_h=7..14`, `grid_w=9..16`,
`rectangles=2..4`) and a constructive slot partition that realizes their full
Cartesian product without retries or dropped rectangles.

The canonical Racket authority was not changed. The generator now pins its
12-hex canonical hash, rejects malformed/blank/singleton/collinear/overlapping
inputs, and declares a semantic contract around the strongest public-only rival:
all five canonical pairs use NW→SE corners, so `main_diagonal_only` fits all of
them. The default schedule alternates canonical-profile NW→SE anchors with
mixed-orientation counterexamples containing both NW→SE and NE→SW pairs. Every
consecutive two-demo window therefore refutes both `main_diagonal_only` and the
broader `homogeneous_orientation_only` rival.

Task-local tests and `workspace/qualify.py` retain the regression and fast
preflight. The source-bound battery and lesson census remain the acceptance
authorities; the workspace probe is intentionally Python-only.


## 2026-10-04 final self-review hardening

A packaging-stage self-review found that version 2.0.0 made each individual
scene orientation-homogeneous. That left a broader canonical-fitting shortcut:
fill all rectangles only when every pair leans the same way, otherwise make no
change. A failing regression was retained in `checks/mixed-orientation-red.log`;
version 2.1.0 now alternates pair orientation inside every counterexample scene,
declares the shortcut and a mixed-orientation witness, and keeps the anchor
profile unchanged. The complete final battery, census, portable tests, and
post-repair solve were rerun against the new source hash.
## Current reviewer considerations

Source SHA-256: `bec34c6fa7ad1c7930222894ffe4d339077bc0a9ac85b90bccc0e2f2aca1ddd2`.

# Decisions for 89c85768abe1

Final selected version: `2.1.0`. Final generator SHA-256:
`bec34c6fa7ad1c7930222894ffe4d339077bc0a9ac85b90bccc0e2f2aca1ddd2`.
Canonical Racket hash: `d273f364d771` (unchanged).

## Evidence basis and prior lead

I used prior return `review-6c4f2053a7aa3c1b:v0001` only as a lead. I then
reproduced its concerns against the pinned selected baseline
`78d36bf63a4d03d39a68b373ca1201df5974851dc6685a2911c529650e08eb8a`.
The before battery measured 7 green, 2 advisory, and 3 failed stages: `lint`,
`defect_lint`, and `override`. The baseline advertised controls it did not read,
allowed texture paths to bypass exact dimensions, accepted an unknown control,
and had a `self_check` too weak to reject impossible lessons.

## Input and contract choices

| Choice | Final decision and rationale | Rejected alternative |
| --- | --- | --- |
| Rule authority | Keep the canonical Racket rule unchanged and pin `RULE_HASH="d273f364d771"`. Canonical outputs and the Python mirror already agreed; the defects were in generation and validation. | Editing the rule would add risk without addressing the measured failures. |
| Public axes | Expose only exact, pixel-observable `grid_h`, `grid_w`, and `rectangles`. | Retaining the nine-axis baseline surface would preserve ignored labels and unverifiable metadata. |
| Height/width | Exact Cartesian domains `grid_h=7..14`, `grid_w=9..16`. These cover canonical sizes and broader lawful scenes, and every boundary combination is constructible. | Difficulty-dependent silent narrowing; it made valid advertised overrides fail. |
| Rectangle count | Exact `rectangles=2..4`. Two matches the canonical anchor; three and four broaden composition while still fitting a constructive partition at the minimum 7×9 grid. | Counts beyond four would either require a different placement construction or hidden incompatibilities at the minimum dimensions. |
| Colors | Sample distinct nonzero ARC colors from 1..9; background remains 0. Color identity is irrelevant to the rule, while distinct colors make pair ownership observable. | Repeated colors would merge multiple rectangles and make the intended pairing ambiguous. |
| Placement | Partition the grid constructively into disjoint slots, then choose a nondegenerate rectangle inside each slot. This realizes all advertised axis combinations without retries, truncation, or dropped rectangles. | Rejection sampling was avoided because it can make exact overrides probabilistic and obscure failures. |
| Pair orientation | Canonical anchors use NW→SE pairs. Counterexample scenes alternate pair orientation internally, guaranteeing both NW→SE and NE→SW pairs in the same grid. | Version 2.0.0 used orientation-homogeneous scenes. A self-review found that this allowed the broader `homogeneous_orientation_only` shortcut; the retained red test is `checks/mixed-orientation-red.log`. |
| Lesson schedule | `EXAMPLES_NEEDED=2`; consecutive sample indices alternate anchor and counterexample profiles. Every two-demo window therefore contains a mixed-orientation rebuttal. | Purely random profile selection could yield complete lessons with no distinguishing witness. |
| Validation | Require 2..4 nonzero colors, exactly two cells per color, row and column separation, pairwise-disjoint inclusive boxes, rectangular grids, domain sizes, and ARC colors. | Counting colors alone accepted blank, singleton, collinear, overlapping, ragged, and out-of-domain impostors. |
| Semantic rivals | Declare both `main_diagonal_only` and `homogeneous_orientation_only`, with executable anti-diagonal and mixed-orientation witnesses. | Treating one canonical ambiguity as exhaustive would leave a stronger generated-distribution shortcut unmeasured. |
| Strict support | `MIN_STRICT_FRAC=1.0`; all lawful draws and all canonical inputs remain on the same semantic manifold. | Lawful “degenerate textures” were removed rather than weakening strictness. |

## Probes and test-first repair

The first regression set was written before the initial repair and failed on the
missing rule pin, ignored controls, weak validator, and absent semantic contract.
After version 2.0.0 passed, final self-review added a new failing regression for
mixed orientations before changing production code; it failed because
`homogeneous_orientation_only` was absent and counterexample grids were
homogeneous. Version 2.1.0 then made that test and the full 10-test task suite
green.

`workspace/qualify.py` is the reusable fast probe for future agents. On the final
source it checked 300 draws (100 per band), 72 exact-boundary override cases,
300 consecutive lesson windows, five malformed fixtures, deterministic replay,
and both witnesses; all 300 draws were lawful and unique. It is deliberately
Python-only and does not replace Racket authority checks.

The final source-bound battery is 12/12 green. The final lesson census
materialized 100/100 lessons in each band, with 900/900 unique inputs, zero
ambiguous lessons, and both declared rivals refuted in every lesson. The task
suite also checks all consecutive two-demo starts 0..17 in every band, covering
cyclic schedule parity beyond the census's non-rotating query policy.

## Failure modes and limitations

- The constructive layout uses stripes for 2–3 rectangles and quadrants for 4.
  It covers all exact public axes and many placements, but not every possible
  arrangement of disjoint rectangles. This is a documented distribution limit,
  not an API claim.
- Finite tests establish behavior for the sampled schedules and declared rivals,
  not universal ARC identifiability. An undeclared rival may still exist.
- All generated bounding boxes are pairwise disjoint. Overlapping same-rule
  rectangles would need an explicit ownership/overwrite policy and are outside
  this generator's domain.
- The catalog remains `approved=false` and `train_safety=unverified`; this review
  does not alter admission status.
- Two final-battery attempts were interrupted by the outer execution harness and
  retained under `checks/final` and `checks/final-rerun`. A third fresh run under
  `checks/final-complete` completed all 12 stages green on the same source hash.

## Final self-review

The main newly introduced risk was the orientation-homogeneous scene pattern;
it was converted into an explicit rival and eliminated by mixed-orientation
counterexamples. The remaining visible restriction is constructive slotting,
but the task's output depends only on each color's bounding box, and the final
census shows both known canonical-fitting shortcuts are refuted in every sampled
lesson.
