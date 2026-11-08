# Native rotation family

This extends the retained clockwise/counterclockwise prototype with a native
adapter and an input-dependent color-count rule. The production generator,
canonical authority and original `prototype.py` remain unchanged.

## Episode rule

| Private `rotation_rule` | Transformation |
| --- | --- |
| `clockwise` (default) | Exact canonical Racket: rotate every object 90° clockwise in its own anchored bounding box. |
| `counterclockwise` | Retained three-quarter-turn Racket variant. |
| `color_count` | Count the L objects of each color, then rotate every L clockwise by that color's count modulo four. |

The setting stays fixed throughout an episode. Inputs and their order are
identical across settings for the same seed and counts. The new rule is
**contextual gating**: a remote same-colored object can change another object's
required rotation. It is not iterative state simulation.

A segments and counts monochrome objects. Its intermediate is the map
`color -> component count`. B uses that map to select each object's turn count.
The wrong-intermediate program in `native.py` substitutes same-color pixel count
divided by three; scale-2 objects make that concrete shortcut differ.

## Domain and constructive teaching

The separate native domain admits 7..30 rows and columns, 2..36 L objects,
scale 1 or 2 (three occupied square quadrants of a 2x2 or 4x4 box), colors 1..9,
and 1..4 objects of each color. Boxes have a full one-cell moat, so all rotations
stay disjoint and inside the canvas. `analyze` validates every component and the
complete geometry. This extends the production sampler's 2..4 unscaled objects
on 7..14 canvases; it does not silently broaden the production validator.

Demonstrations and queries are independent: 2..6 demos, default 3, and 1..4
queries, default 4. The first two demos share ten object positions, orientations
and sizes. Recoloring one remote L changes color multiplicities from
`[1,2,3,4]` to `[1,1,4,4]`. Four otherwise unchanged objects then rotate
differently under `color_count`. The unchanged colors supply controls.

Mixed scales in those first two demos reject pixel-count substitutes. Missing
counts in the second demo reject count-rank substitutes. Adjacent missing-corner
orientations distinguish rotations from fixed reflections, including a
reflection selected separately for a given count. Color 6 and other colors are
present in every minimum teaching pair. Exactly equivalent descriptions of L
rotation are not considered ambiguities.

Queries are distinct and novel relative to the demonstrations:

| Query | Canvas | Scale | Objects | Nonzero cells |
| --- | --- | --- | --- | --- |
| 1 | 7x7 | 1 | 4 | 12 |
| 2 | 14x18 | 1 | 10 | 30 |
| 3 | 24x26 | 2 | 16 | 192 |
| 4 | 30x30 | 2 | 25 | 300 |

Each query places an object's bounding box at every canvas corner. At 30x30, 21 of 25 objects rotate to a
different orientation under the count rule; all 25 must be counted. The first
query is independent of the requested total query count. Input construction is
finite, with no rejection/retry loop or silent truncation.

## Model-visible projection

`adapter.model_view(episode, query_index)` returns only demonstration input/output
pairs and that one query input. It deep-copies explicit public fields and omits
settings, seeds, programs, query answers, future query inputs and total-count
hints, including extra metadata attached to a pair. The existing consumer remains
responsible for revealing one query after the preceding answer. The four-query
controller record is private. Public filenames hash exactly the visible bytes
from `reviewer_support.public_challenge_bytes`.

## Reusable bounded audit

From the packet outer folder containing `review.py`:

```bash
python3 review.py run python3 generators/371eb0221101/workspace/parametric/audit.py \
  --out ../checks/371eb0221101/new-audit
```

Use the passing Python environment, e.g. `WORK/.venv/bin/python`. The tool refuses
an existing output directory; optional repeated `--seed` flags accept one to four
distinct seeds. Defaults are 0 and 17 at demo counts 2 and 6 for all three settings.
It executes every claimed label through protected Racket, caches identical
program/input evaluations, checks 44 declared hypotheses on demonstrations only,
checks query disagreement, and writes hash-named first-turn public challenges.
The receipt retains minimal teaching pairs, source hashes and exact scope.

Current checked evidence: 39 native tests plus 3 retained-prototype tests; 18 audit
episodes at seeds 0, 17, 121, with 144 label claims checked by 90 distinct protected
executions; 44 finite hypotheses with only the selected setting surviving; 18 saved first-turn exports
passed the independent public checker. See
`evidence/current/self-review-summary.json` and returned
`checks/371eb0221101/self-review-final/report.json`.

A review found a seed 121 minimum-demo column-count shortcut in the first
implementation. The four count-4 objects now form a 2x2 rectangle, making each
row/column count exactly 2, unlike their intended 1, 3 or 4 turns. This is a
constructive fix; the seed 121 regression and the final audit include it.
The audit now retains exact executed program bytes and hashes.

The original interrupted evidence remains historical and is not a current pass.
The retained legacy command still produces its original 3-demo/1-query prototype:

```bash
python3 review.py run python3 generators/371eb0221101/workspace/parametric/prototype.py \
  --seeds 0 2 --difficulty easy --out-dir ../checks/371eb0221101/legacy-example
```

## Owner handoff

`promotion.json` exposes the three settings. The native manifest inventories the
adapter, extension, retained prototype, audit, tests and compact current evidence.
Native qualification and the protected wrong-intermediate witness are returned
under `checks/371eb0221101/qualification/` and `checks/371eb0221101/causal/`.
After integration, the owner must qualify and accept the exact live bytes before
using the family in accepted exports. This reviewer return grants neither owner
acceptance nor training admission. The finite checks do not prove all seeds,
all possible hypotheses, arbitrary polyomino support or learning benefit.
