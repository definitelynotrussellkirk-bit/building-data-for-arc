# First input-blue component: native parametric family

This opt-in family keeps the two red endpoints, the canonical rounded DDA, and
its conditional line colors. Its one episode-fixed parameter is:

| `reach` | Executed behavior |
| --- | --- |
| `line_only` (default) | Return the exact canonical program; path black becomes red and path blue becomes green. |
| `first_blue_component` | Draw that same line and recolor the entire four-connected **input-blue** component containing its first blue hit to green. |

The first endpoint is the row-major first red cell. The DDA visits indices
`0..max(abs(dr), abs(dc))`; interpolation computes `t = float(i)/float(steps)`
before multiplying `t` by either delta. Arithmetic must not be reassociated:
that changes some floating half-step ties. Both implementations use ties-to-even
rounding. A line with no input-blue hit has the canonical output.

## Causal composition

Step A traces the endpoint-defined DDA in order and binds the first input-blue
hit. That input-dependent coordinate selects its four-connected component in
the unchanged input. Step B paints that selected component green in the line
result. Off-path component cells cannot be selected until A supplies its hit;
neither globally selecting a blue object nor discovering connectivity after
line painting implements this rule. The Racket alternative uses `objects g 0`,
`obj-cells`, and `paint-cells`, preserving original-input connectivity.

## API and input sampling

`adapter.py` exposes `program(settings)`, `generate(seed, settings, demos=3,
queries=4)`, and `solve_python(grid, reach)`. It loads `prototype.py` by its exact
adjacent path under a task-specific module name. No production generator or
approval changes are part of this adapter.

Requests support exact integer seeds `0..2**63-1`, 2–6 demonstrations, and 1–4
queries independently. Invalid seeds, counts, setting values, and extra setting
keys raise `ValueError`. Every sampled input has dimensions 5–30, exact integer
colors from `{0,1,2}`, and exactly two red endpoints. The rule is total over
such inputs, including adjacent endpoints and no blue intersections; the
sampler deliberately produces visible transformations.

Input sampling does not inspect `reach`. Separate deterministic per-index
demonstration and query streams preserve demonstration and query prefixes when
counts change. All episode inputs are distinct. The first two demonstrations
are constructed directly: a shallow oblique line has a small first-hit component
before a larger later-hit component, and a steep oblique line reverses that size
relationship. The steep demonstration has both red endpoints inside the canvas,
so its unchanged cells beyond the endpoints distinguish a finite segment from
extending the DDA line to the grid edges even at the minimum two demonstrations.
Both have
off-path component arms, a diagonal-only neighbor of the chosen component,
black line cells, and untouched distractors. Dimensions, line placement, arms,
and exterior texture vary by seed. Additional demonstrations include oblique
down-left geometry.

Four queries cover a substantive 30×30 textured canvas, a shallow down-left
12×23 line, a steep 25×11 line, and a 19×27 line with interior endpoints. The large scene has
random dense blue texture across the canvas; cardinal black moats keep the
explicit first and later touched components separate. Those components each
have an off-path arm. All four query scenes have independently sampled arms and
texture. Literal 5×5 cases in the focused tests exercise the minimum size with
off-path expansion and diagonal-only neighbors, separately from ordinary queries.

## Run

From the outer extracted review directory, emit a private complete episode:

```bash
WORK/.venv/bin/python review.py run python3 \
  generators/55ba26e599d3/workspace/parametric/prototype.py \
  --seed 17 --reach first_blue_component --demos 3 --queries 4
```

The emitted JSON includes private settings through its program identity and
query labels. Use the native exporter for a public challenge; public names and
bytes must be derived only from demonstration inputs/outputs and query inputs.
Do not publish the standalone command's full output as a challenge.

The saved four-query public container is controller data. On each model turn,
project only `train` and a one-element `test` containing the current query
input; reveal the next query after the preceding answer. Do not include the
total number of queries, future inputs, final-turn hints, hidden settings,
reference programs, or query answers. The first-turn visible bytes are identical
whether generation requested one query or four. Evaluation can stop after the
first answer without changing that first turn. The existing
`reviewer_support.public_challenge_bytes` helper gives the canonical visible
projection and content-derived naming bytes for a supplied one-query turn.

Focused behavioral regressions:

```bash
WORK/.venv/bin/python review.py run python3 -m pytest -q \
  generators/55ba26e599d3/tests/test_parametric_first_hit.py
```

The default resource `canonical.rkt` is the exact `program_solution` string
from the canonical JSONL authority for `55ba26e599d3`, including whitespace.
The nearby base solution's one-line source is semantically equivalent but is
not the native byte-authority. Both Racket resources are explicitly declared in
`promotion.json`. Native inventory, protected qualification, and exact-source
owner acceptance remain separate gates; Python checks alone do not approve
this family or admit its examples to training.

The finite teaching audit covers declared settings and the explicit rivals in
the retained evidence. It does not establish uniqueness against arbitrary
programs or all future seeds. The four-query command, canonical source binding,
Racket replay, causal witness, and actual native qualification receipts are
retained by the review workflow rather than inferred from this README.
