# Stamp-transform native family

This task-local family reads every cyan cell relative to the single green
anchor, clears the scene, and stamps those offsets at every red destination.
The hidden `stamp_transform` remains fixed throughout an episode:

| Setting | Meaning |
|---|---|
| `identity` | Transplant the observed offsets unchanged. This is the exact canonical default. |
| `mirror_horizontal` | Negate each horizontal offset around the green anchor before transplanting it. |

Copies combine by union. Cyan cells covered by two or more copies remain cyan;
holes and thin parts are not filled. The original source, green anchor and red
markers are cleared unless the resulting cyan stamps independently cover those
coordinates. This extension changes input support, not either setting's rule.
It does not edit the production generator, its version `3.1.1`, or its selected
canonical authority. The production finite-bank count-lookup audit remains a
separate unresolved finding.

## Native API and grammar

`adapter.py` loads the adjacent `prototype.py` by exact path and delegates to
its implementation. `promotion.json` declares both settings, the canonical
default, two through six demonstrations, one through four queries, and three
demonstrations for ordinary qualification. The Python entry points are:

```python
normalize_settings(settings=None)
program(settings=None)
facts(grid)
self_check(grid)
reference(grid, settings=None)
generate(seed, settings=None, demos=3, queries=4)
```

`None` and `{}` select `{"stamp_transform": "identity"}`. Non-dictionaries,
unknown keys, extra keys, non-string setting values and undeclared settings
are rejected. Seeds must be exact nonnegative Python integers; counts must be
exact integers in their declared ranges. Booleans, strings and floats are not
coerced. The native framework may choose a declared setting from the episode
seed; `generate` itself uses the setting it receives.

The admitted native input grammar is a rectangular list of lists with both
dimensions in **8..30**, exact integer colors **0, 2, 3, 8**, exactly one green
anchor, at least one cyan source cell, and at least one red destination. Green
plus cyan must form one eight-connected component. Every full stamp must fit at
every red destination under **both settings**. Red input cells cannot replace
source pixels because each input coordinate has one role. Stamps may overlap
each other and may cover source or marker coordinates in the output.

There is no finite template-membership test and no count-to-shape lookup.
`facts` returns JSON-safe dimensions, green/red/cyan coordinates, the complete
observed offset list, source bounding box, counts, and grammar errors. `reference`
accepts smaller lawful canonical/legacy grids as well; the eight-cell lower bound
is a native sampling/admission restriction, not a change to transplantation.

`program` reads the retained `canonical.rkt` bytes for identity. For horizontal
reflection it changes the single checked horizontal-offset expression. Python
labels are deterministic claims. Native qualification and export must execute
the exact program in the protected Racket worker; Python agreement alone does
not establish executed labels or acceptance.

## Procedural source geometry and teaching

The native sampler grows cyan cells from three kinds of scaffold: rectangular
rings, thin branches and connected walks. Its random growth, dimensions,
cardinality and noncentral green anchor produce many offset sets of the same
count. Ring growth excludes the green cell and a reserved black interior cell.
Branch growth prefers one-cell-wide additions. Every emitted source is
connected, and every sampled pair has different identity and mirror outputs.

The first two demonstrations are a controlled geometry intervention. They have
identical canvas dimensions, green coordinates, red coordinates and cyan count,
but different source offset sets and different labels under each setting. They
therefore refute any deterministic rule that uses only cyan count and the
destination coordinates. Both demonstrations include multiple destinations,
even-multiplicity overlap, offsets beyond a local 3×3 neighborhood, and source
pixels that disappear from the output under both settings. Their green anchor
is neither the cyan bounding-box center nor its top-left corner.

The other four available demonstrations add branch/walk/ring shapes, a
single-destination example, more destinations and different rectangular fields.
Only the requested demonstration prefix is exposed. The independent audit checks
the minimum two-demo prefix against the other setting and thirteen explicit
shortcuts; query labels are not used to select the certificate's survivors.
This bounded rival set is evidence of the declared distinctions, not a proof
that no other fitting program exists.

## Independent query prefixes

Every seed constructs a fixed bank of six demonstration inputs and four query
inputs **before** the requested counts are sliced. Inputs do not depend on the
selected setting, demonstration count or query count. Repeating a seed and
settings is deterministic. All ten bank inputs must be distinct; any failed
construction raises an error instead of returning a short episode.

| Query slot | Canvas and content |
|---|---|
| 0 | The lawful minimum, 8×8; a grown 3×4 branch with 6–8 cyan cells and two overlapping destinations. |
| 1 | A seed-varied 12–16 by 17–21 rectangle; a grown connected walk and one destination. |
| 2 | A seed-varied 20–24 by 21–27 rectangle; a grown 5×7 ring and three fully separated destination regions under both settings. |
| 3 | Exactly 30×30; a grown 7×9 ring with 40–47 cyan cells and 12–16 destinations. Its outputs contain at least 150 cyan cells, span rows 0 through 29, and span at least 25 columns under both settings. |

The large query is populated across the canvas, including boundary placements;
its size is not created by padding a small unchanged example. Single, separated
multiple and overlapping destinations all remain available within one family.

Each of nine profile groups has a hard limit of **128 deterministic candidate
attempts**. The paired teaching group grows two candidate shapes per attempt;
the other eight groups grow one each. A failed shape/layout is counted and the
next attempt uses its own keyed RNG stream. There is no unbounded retry loop.
The mathematical worst-case caps are 1,280 shape constructions and 1,152 layout
attempts per full bank. Observed attempts, output counts and even-overlap counts
are retained under private `meta.generation`; the paired layout is counted once,
with the second demonstration explicitly referencing its shared layout.

## Compatibility and evidence

`build_input`, `generate_episode`, `racket_program`, `apply_rule` and the original
bounded evidence helper remain available. The first two retain their legacy
hook/stair input schedule and original three-demo/one-query defaults, including
their historical finite-bank limitation. `apply_rule` now calls the shared
geometry-based reference, so both legacy and native scenes use one Python rule.
The new native adapter calls `generate`; it does not silently change legacy
episodes or use the old evidence report as native evidence.

Focused behavior tests are in
`tests/test_native_family_8de1c257a9c7.py`; legacy compatibility remains covered by
`tests/test_parametric_stamp_transform_8de1c257a9c7.py`. Run from the packet root
with a fresh receipt path:

```sh
WORK/.venv/bin/python review.py run \
  --receipt checks/8de1c257a9c7/native-tests-command.json \
  python -m pytest -q \
  generators/8de1c257a9c7/tests/test_native_family_8de1c257a9c7.py \
  generators/8de1c257a9c7/tests/test_parametric_stamp_transform_8de1c257a9c7.py
```

`audit_native.py` independently extracts geometry, executes the settings and
declared rivals, and evaluates demonstrations before revealing query checks.
`check_geometry_gate.py` is the opt-in same-count demonstration gate associated
with the assigned data-value question. `make_examples.py` creates hash-bound
controller payloads, private labels and one-query actor payloads for the existing
consumer. Their local source, tests and retained receipts document the
actual bounded runs. Historical evidence remains historical; current native
acceptance is determined by fresh source-bound qualification and acceptance,
and does not imply downstream training admission or measured learner benefit.

The geometry gate consumes an episode, an episode list, or the export's private
metadata JSONL. It uses demonstrations only and compares supplied labels without
re-executing them. After native label verification, a typical invocation is:

```sh
WORK/.venv/bin/python review.py run python3 \
  generators/8de1c257a9c7/workspace/parametric/check_geometry_gate.py \
  ../checks/8de1c257a9c7/examples/private/metadata.jsonl \
  --require-contrast --out ../checks/8de1c257a9c7/geometry-gate-examples.json
```

This strict contrast is sufficient to refute count-and-destination-only rules;
it is not necessary for every useful task. An intentionally finite-template
family or a diverse lesson without exactly matched nuisance features can fail
the gate. Enable it for families intended to teach reading arbitrary geometry.
