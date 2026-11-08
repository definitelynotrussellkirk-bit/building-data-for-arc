# Shorter-first elbow routing — proposed native family

`routing=canonical` returns the byte-exact selected reference rule: for each
color in original reading order, connect its upper endpoint vertically then
horizontally, painting onto an initially empty canvas. Canonical collisions use
that source's paint/overwrite order, not a Python replacement authority.

`routing=avoid_shorter` orders pairs by Manhattan distance, breaking ties by the
upper endpoint's row-major position. For each pair it prefers a clear vertical-
then-horizontal elbow; if occupied, it uses a clear horizontal-then-vertical
elbow. If both are blocked, its total fallback is vertical-first. Generated
scenes always have at least one clear option; the fallback is tested separately
but is not taught as a branch of the sampled curriculum.

## The dependency

A routes earlier, shorter pairs and produces an occupied path grid. B tests its
candidate elbows against that grid, including intermediate cells that were not
endpoints in the input. Merely checking original endpoints gives the wrong
answer. The source-bound witness uses the same shortest-first order but replaces
occupancy with an empty grid, changing a later bend and the final answer.

The first lesson deliberately makes the interfering pair *not* the longest and
makes rectangle-area and width priorities disagree with Manhattan distance.
The second makes height priority disagree. Median/min/max color role swaps refute
color-priority rules. Both lessons include a third noninterfering path. Horizontal
reflections, palette changes, several constructive geometry choices, scale, and
additional independent endpoint pairs vary inputs while keeping one fixed rule.

## API and limits

`generate(seed, {"routing": MODE}, demos=3, queries=4)` supports integer seeds >=0,
2..6 demonstrations and 1..4 queries. The intended authoring request stores four
queries; all shorter requests are exact prefixes. Inputs are matched across
settings. Sampling depends on seed, split and pair index, never demo/query counts.
Unknown settings and coercive integer requests fail closed.

Generated inputs have 3..9 colors, each with two endpoints on different rows and
columns. The rule also handles 2-color examples. Sizes range from 10x13 to 30x30.
The 30x30 query contains all nine endpoint pairs, spans all four edges and
produces at least 272 colored output cells in the retained 32-seed audit. Sparse
input endpoints are intrinsic to this task, not an empty padding frame.

The production generator and canonical authority are unchanged. Unlike the
production generator's 9..12 by 10..13 disjoint canonical paths, this separate
parametric grammar permits canonical path collisions and extends canvas size and
pair count. The avoidance variant resolves the constructed conflicts without
blocking both candidate elbows. It is not a general shortest-path search, and
there is no claim of exhaustive collision topologies.

`public_turn_bytes(episode, index)` exports only train input/output pairs and one
test input through the native serializer. Exact serialized bytes define the public
hash name. No private settings, program, query output, future input, ordinal or
total-query hint is exposed. No training loop or turn controller is added.

## Reproduce from the packet root

```sh
python3 review.py run python3 generators/2dae2c34641b/workspace/parametric/audit.py --seeds 32 --out ../checks/2dae2c34641b/new-audit
python3 review.py task-tests 2dae2c34641b --phase after --out ../checks/2dae2c34641b/new-tests
python3 review.py run python3 -m arcpuzzles parametric qualify 2dae2c34641b --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/2dae2c34641b/new-qualification --summary
```

Current bounded evidence: 36 staged task tests; 320 episodes / 2,560 labeled-pair
checks / 319 distinct inputs; 17 finite policies; 55 protected Racket executions;
16 public files. No query-disagreeing survivors or sampled fallback cases. Some
reading-/reverse-distance-priority rivals agree with canonical outputs throughout
this restricted grammar; they are reported as survivors, not falsely rejected.
No tested rival survives the alternate setting. The tie/fallback fixture is
explicitly outside the sampled grammar. This is author self-review, not universal
identifiability, an independent review, measured learning benefit, owner acceptance
or training admission.
