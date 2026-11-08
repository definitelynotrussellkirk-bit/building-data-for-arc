# Matching or opposite wall: task-local parametric prototype

This prototype exposes one private episode parameter while preserving the
selected canonical generator and rule. Native qualification and owner acceptance
are separate steps; the Python functions below supply claims for independent
protected Racket execution.

| `wall_relation` | Transformation |
|---|---|
| `matching` (canonical default) | A piece moves toward the wall with its own color. |
| `opposite` | A piece moves toward the wall with the other color. |

`program({"wall_relation": "matching"})` returns `canonical.rkt` byte for byte.
That resource is copied from the unique selected Catalog `program_solution`.
The opposite program replaces the one expression
`(list (list lw -1) (list rw 1))` with
`(list (list lw 1) (list rw -1))`. Every other byte stays unchanged.
The exact-default test resolves the selected `rule_task_id` through the Catalog.

## Rule and admitted inputs

All sampled grids are between 9×9 and 30×30. Color 7 is the background. The
left and right columns are full-height, constant walls with two distinct
non-7 colors. Both colors occur inside the walls, and no third foreground color
occurs. Colors are selected from all nine non-background ARC colors, including
0; the relation is relative to the visible walls, rather than a fixed palette.

Objects are maximal same-color **8-connected interior** components. Wall cells
are excluded when finding objects, so an interior piece may initially touch a
wall. The unchanged program discovers objects in row-major order, then stably
sorts each color's objects nearest its destination first. It processes the entire
left-wall-color group before the right-wall-color group under both settings.
For each piece, it scans from every original cell along its horizontal travel
direction in the partly constructed result. The minimum free distance determines
one translation applied to the entire shape. Walls and already settled pieces
therefore stop later pieces; background and unprocessed original pieces do not
act as blockers in that result.

The sampler adds a shared safety condition for **both** settings: no original
piece position is occupied by a previously settled piece when its turn begins,
no translated piece overwrites a previously settled cell, and every color's cell
count is conserved. `validate_grid` checks that condition under both directions.
It excludes a real canonical edge case in which a wide settled shape covers the
starting position of the other color. It does not change the authority's scan
or update order. `solve` remains an exact claim mirror on structurally valid
grids, including that edge case; it is not the admitted-grammar validator.

The main sequential dependency is retained without adding a new operation:

1. **A:** settle the nearer member of a same-color queue against the wall or the
   existing settled pieces.
2. **Input-dependent intermediate:** the rows and columns occupied by that
   newly settled shape, determined by its shape and preceding blockers.
3. **B:** scan and settle the next queued rigid shape against those new cells.

B's minimum allowable translation depends on A's actual settled silhouette.
The `independent_no_blocking` Racket rival skips that intermediate and gives a
different final grid on the teaching queues. The separate source-bound causal
witness and native replay are produced by the review workflow.

## Sampling and teaching

The first two demonstrations are constructed teaching scenes. Each has a
diagonally connected piece, a distinct queued follower of the same color,
both wall-color roles, and a middle band containing both colors. In one scene
the outer queues start near their matching walls; in the other they start near
the opposite walls. Reflections, follower shapes and offsets, wall colors,
middle shapes and canvas dimensions vary by seed.

The two-demo selection checks **both parameter settings** against seven finite
rivals: the other relation, independent wall-only movement, cellwise packing,
4-connectivity, identity, nearest-wall direction, and farthest-wall direction.
Every selected lesson rejects every rival using demonstrations alone. The
position-based rivals keep the selected rule's object ordering but choose each
piece's direction from its mean starting column; a midpoint tie chooses right
for nearest and left for farthest. `rivals.py` provides executable Racket versions
for an independent teaching audit. These finite rivals do not establish unique
identifiability among arbitrary programs or measured learning benefit.

Additional demonstrations use different dimensions and independently sampled
shape collections. Query profiles are fixed by their index:

| Query | Canvas | Constructive content |
|---|---:|---|
| 0 | 9×9 | Six compact pieces; mixed-color band, two same-color queues, edge rows. |
| 1 | 16×20 | Ten pieces across four bands with ragged and diagonal shapes. |
| 2 | 24×27 | Sixteen pieces across four widely separated bands, including mixed-color queues. |
| 3 | 30×30 | Twenty-four pieces across six bands, with both colors in half the bands. |

The largest profile reaches both edge rows and the first and last interior
columns. Its pieces include irregular polyominoes, diagonal-only connections,
different silhouettes and multiple same-color queues. It requires at least
110 interior colored cells, at least 22 occupied rows, and at least 100 changed
cells under each setting. Empty padding cannot meet these postconditions.
The row-band construction is a bounded grammar, not unrestricted arbitrary
interleaving. The bands contain genuine packing interactions; larger boards
increase object count as well as available space.

Input RNG streams depend on the seed, split, index and bounded retry number.
They do not use the selected parameter, requested demo count, or requested query
count. Thus the same request across settings has identical inputs, extending
one split preserves its prefix and the other split, and a one-query run has the
same first query and demonstrations as a four-query run. All inputs within an
episode must be distinct. A draw has a cap of 64 attempts, with a clear error
if construction or teaching fails; it never silently reduces counts or inserts
a weaker fallback. `sample_inputs(...)["attempts"]` exposes the actual attempts
for private diagnostics. The first two entries refer to their joint lesson
selection attempt.

## API

`adapter.py` loads `prototype.py` by its exact adjacent path, without relying on
an ambient module named `prototype`. It exports:

```python
program(settings) -> str
generate(seed, settings, demos=3, queries=4) -> dict
```

Settings must be an exact dictionary with only `wall_relation`, whose value
is exactly `matching` or `opposite`. Seeds must be exact Python integers in
`0..2**63-1`; booleans, coercible strings and floats are rejected. Demo counts
are independently supported from 2 through 6, and query counts from 1 through
4. Counts must also be exact integers. The ordinary qualification uses three
demonstrations and four queries.

The result contains `train`, `test`, and `program_solution`. Both splits contain
input/output pairs and are **private authoring data**. Native generation checks
each claim with the returned Racket program. `prototype.py` additionally exposes
`sample_inputs`, `solve`, `validate_grid`, `components`, `rival_names`,
`solve_rival`, and `demo_rival_failures` for focused checks.

## Run from the extracted packet's outer folder

The commands below use the packet's installed interpreter and `review.py` to
select the bundled Racket runtime and repository working directory. Output paths
given to payloads are relative to `WORK/repo`; use a fresh output directory.

```bash
WALL_PY="$PWD/WORK/.venv/bin/python"
"$WALL_PY" review.py run "$WALL_PY" -m unittest discover \
  -s generators/4295e17d5995/tests -p test_parametric_4295e17d5995.py -v

"$WALL_PY" review.py run "$WALL_PY" \
  generators/4295e17d5995/workspace/parametric/audit.py \
  --out ../checks/4295e17d5995/audit-new
```

The audit runs both relations at the minimum and maximum demo counts, always
with four queries, independently checks the seven Racket rivals, and writes
private execution evidence plus public examples. Its public first-turn projection
contains only demonstrations and the current query input. Query answers, future
queries, parameter settings, source programs and sampler diagnostics stay private;
an episode container with four queries is controller data, not a complete prompt.

After the native source/evidence inventory is current, qualification is:

```bash
"$WALL_PY" review.py run "$WALL_PY" -m arcpuzzles parametric qualify \
  4295e17d5995 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/4295e17d5995/qualification-new --summary
```

Fresh owner qualification and acceptance must bind the integrated source bytes.
The canonical generator is outside this prototype's change scope. Focused tests,
bounded native jobs and the causal witness establish only their recorded scope;
they do not admit trajectories to training or change dataset mixture weights.
