# Native ring-motion family

## Design

Goal: preserve the exact canonical ring permutation while adding its inverse and
two per-ring, input-dependent choices between those permutations. The source
authority moves corners counterclockwise and edge midpoints clockwise; the old
English description is not an executable specification.

The implementation stays in `prototype.py`, with a thin adjacent-path loader in
`adapter.py` and bounded requests in `promotion.json`. It uses Python standard
library sampling and emits standalone Racket rules for independent execution.
The selected canonical generator and ledger remain the authority for default
bytes and official examples. This packet is not a Git checkout; the native
delta builder records source changes.

Settings under `ring_motion` are `canonical`, `inverse`, `odd_canonical` and
`even_canonical`. In the conditional modes, step A counts distinct colors in
each detected ring's eight border cells, including zero. Step B consumes that
count's parity to select the canonical or inverse mapping. This is contextual
gating; it is not a claim of iterative state simulation.

Implementation choices: a direction-only extension would omit the required
input-dependent decision. A moving external marker would change the original
object grammar. Per-ring color diversity retains the source objects and can
require different operations within one input.

Review focus: zero is a real border color; counts must be local to each ring;
source values must come from the original input; rings must be separated;
query-count changes must not reveal future inputs or change the first turn.

## Grammar and teaching

All background and centers are orange (7). Every generated ring has eight
non-7 border cells and a full background separator from other rings. The native
sampler uses the finite profiles below, bounded within 7–30 rows and columns; the semantic rule also supports isolated
3×3 anchors. One-color rings are lawful but cannot identify direction.

The first two demonstrations mix odd/even color counts, repeated colors and
zero, and differ in ring count and global palette size. The same seeded input
plan is used across all four settings. A bounded, demonstration-only check
rejects a teaching core if any declared or tested extra rival remains viable.
The finite rival list is explicit in `candidate_programs()`; it cannot prove
uniqueness against arbitrary programs.

The API independently accepts 2–6 demonstrations and 1–4 queries. All four
queries are distinct and novel; larger scenes contain many distributed rings.
`public_challenge_bytes` exposes demonstrations and exactly the first unlabeled
query. Remaining queries, answers, settings and programs stay private. Public
IDs depend only on those visible bytes. The existing controller owns later
query reveals.

## Coverage and limits

| Stream | Dimensions | Placement and content |
|---|---|---|
| Core demonstrations | 7×15 and 11×15 | Fixed positions and distinct-count/zero-membership profiles; randomized palettes and border arrangements |
| Extra demonstrations | 11×13, 13×15, 17×19, 21×23 | Separate seeded streams, used in prefix order |
| Queries | 7×9, 13×17, 23×27, 30×30 | Separate seeded streams, four corner rings and roughly 70–100% of separated slots |

Later scenes use a Cartesian product of separated row and column slots, with
spare space distributed among internal gaps. This is a bounded sampler, not
coverage of every size or legal layout. The teaching core permits at most 64
attempts and raises explicitly on exhaustion. No mathematical all-seed success
claim is made. Source inspection and an independent finite review found no
critical/important issue; retained executions are the evidence for measured
success, not that broader claim.

The exact default program also matches all four official labeled pairs. The
retained authoring probe passes 972 protected Racket evaluations over 44 candidate
programs and 26 inputs: eight standard lessons, 32 count-boundary requests,
four official pairs and two separate minimum 3×3 anchors. The 30×30 queries at
seeds 0 and 17 contain 49 and 40 rings (392 and 320 non-background cells),
respectively, spanning all rows and columns. All 40 extra rivals are eliminated
by the demonstrations in these checked lessons. The focused task suite passes
56 tests and four canonical-example subtests.

## Reproduction and handoff

Use the packet's own Python 3.12+ environment with pytest, NumPy and Pillow,
and its bundled protected Racket setup. From the packet's outer folder:

```sh
python3 review.py task-tests 630d6cc550e4 --phase after --out ../checks/task-tests-new
python3 review.py run python3 ../checks/630d6cc550e4/probe.py --out generators/630d6cc550e4/workspace/parametric/evidence/new-run
python3 review.py run python3 -m arcpuzzles parametric qualify 630d6cc550e4 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/qualification-new --summary
```

The native source inventory is created after authoring evidence is stable.
`WORK/RESULTS.json` and `WORK/checks/630d6cc550e4/qualification/` record the
reviewer's qualification; owner acceptance must be freshly replayed against
integrated live source. Neither qualification nor this README admits training.

The saved public files and `public_challenge_bytes` implement the first-turn
projection and use the native canonical serializer, including its final newline.
The shared native exporter still materializes all test inputs; it does not call
this task-local projection. A consumer must use the existing controller's
single-query reveal with this projection. No shared exporter, turn controller,
training reader or production admission was changed by this return.
