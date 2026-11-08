# Selected frames and global enclosure completion

This separate native family proposes a parameterized extension of the selected
task. The production generator, canonical authority, existing approval and
training-admission state remain bound to their existing source bytes.

## Rule and sequential dependence

`{"completion_mode":"border"}` returns the byte-exact selected canonical Racket
program. Find 4-connected green (`3`) components. Select a component precisely
when its height and width are at least three and its cells equal the complete
border of its own bounding rectangle. Paint those selected cells orange (`7`).
Solid blocks, open frames, thin lines, irregular loops and frames with attached
branches fail this predicate. Detached contents do not change the border object.

`{"completion_mode":"enclosed"}` performs that same first stage. Its second
stage treats **only the resulting orange cells as barriers**, floods every
non-orange boundary cell using four-neighbor connectivity, then paints every
unreached zero red (`2`). Surviving green cells are passable during reachability
and retain their color. This is a simultaneous fill based on the completed
first-stage canvas, not an incremental scan through painted red cells.

The orange mask is computed from recognized components. A green irregular loop
does not become a barrier merely because it encloses a hole. Conversely, four
3×3 frames touching diagonally can jointly enclose a central 3×3 pocket outside
each individual frame's bounding box. On the 9×9 authored cage, stage A makes
32 orange cells and stage B makes 13 red cells: four frame centers plus that
central nine-cell pocket. Running stage B on the original input sees no orange
barriers and fails this completion. The native causal witness records and
replays this dependence with a complete counterfactual Racket program.

## API and input grammar

`program(settings)` returns a full `(rule! ...)` program. `generate(seed,
settings, demos=3, queries=4)` returns private complete `train`, `test`, and
`program_solution`. `mirror`, `first_stage`, `second_stage`, and `analyze` expose
Python implementations and diagnostic intermediate state. Protected Racket
execution, rather than Python agreement alone, supplies executable evidence.

Settings contain exactly `completion_mode` with value `border` or `enclosed`.
Seeds are exact integers in `0..2**63-1`; demonstrations independently range
from 2 through 6 and queries from 1 through 4. Unknown keys, bool/float
coercions, invalid counts and malformed inputs are rejected. Semantic inputs
are rectangular exact-integer grids in colors 0 and 3, with each dimension
1..30. No diagonal moat is required in this proposed family. Both rules
commute with all eight square-grid rotations/reflections, with rectangular
dimensions exchanged on quarter turns. This symmetry does not imply that the
sampler emits every legal grid.

## Constructive lessons

Two core demonstrations teach both settings. The first is 9×11 with a
full-width exact frame, a smaller frame, an open frame, a solid block and a
thin line. Exterior zeros occur on both sides of the full-width barrier, so
using only the top boundary for flood seeds is insufficient.

The second is 29×29 with six independently transformed and permuted 9×9 tiles:
the collective cage; nested frames with detached green contents; a stepped
closed loop; an outward branch; an open border and equal-perimeter geometric
spoof; and an inward branch with diagonal contacts. A separate full-height
frame covers the complementary orientation. Together they expose multiple
sizes, tall and wide geometry, frame selection at the boundary, nonrectangular
enclosed regions, collective pockets, and preserved internal contents.
This strong two-example teaching basis has a deliberate context cost: one
core demonstration is large. It is not presented as a minimal pedagogical
layout or a measurement of model learnability.

Extra demonstrations use 13×17, 17×21, 23×27 and 27×29 profiles. The four private
queries use 9×11, 17×21, 25×29 and 30×30, in a separately shuffled order. Small
queries can contain no selected frame; large queries contain substantive
foreground in all quadrants and boundary-reaching shapes. Query construction
does not inspect rival predictions or demonstration outputs. Separate local
RNG streams make inputs matched across settings, counts prefix-stable and
returned arrays fresh. Constructive duplicate avoidance has an explicit
64-attempt bound rather than silently shortening an episode.

`rivals.py` supplies an independent Python oracle, authored controls and full
executable Racket alternatives. Its 28 border and 40 enclosed names are a
finite search grammar. Per-frame bounding-box filling and eight-neighbor
exterior filling share an observed signature on the current controls; reports
retain that alias rather than claiming 68 distinct independent mechanisms.
`audit.py` fits rivals only to demonstrations, then checks queries only for
survivors. It also checks source bindings, canonical identity, native labels,
count prefixes, D4 transformations and a substantive independent 30×30 grid.

## Reproduce and expose one query at a time

From the supplied packet's outer folder:

```sh
WORK/.venv/bin/python review.py task-tests cae2423a6477 --phase after --out ../checks/cae2423a6477/task-tests-replay
WORK/.venv/bin/python review.py run python3 generators/cae2423a6477/workspace/parametric/audit.py --out ../checks/cae2423a6477/semantic-audit-replay.json
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify cae2423a6477 --seed 0 --seed 17 --demos 3 --queries 4 --out ../checks/cae2423a6477/qualification-replay --summary
WORK/.venv/bin/python review.py preview-public export --qualification ../checks/cae2423a6477/qualification-replay/qualification.json --out ../checks/cae2423a6477/preview-replay
WORK/.venv/bin/python review.py preview-public verify --bundle ../checks/cae2423a6477/preview-replay
```

Use new destinations and a current native manifest. A consumer receives only
one `preview/public/<hash>.json` at a time. Programs, parameters, seeds, query
answers and other query inputs remain private. The reusable packet-local
`checks/projection_edges.py` checks these projection boundaries and verifies
rejection of injected answers and unexpected public files.

All reported semantic coverage is finite and source-bound. It does not prove
universal identification, all-seed sampling success, training gain or owner
acceptance. Native qualification and reviewer evidence prepare that subsequent
owner decision without making it.
