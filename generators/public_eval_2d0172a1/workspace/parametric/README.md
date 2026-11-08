# Compact contour diagrams

This unapproved family implements the exact public parent `2d0172a1`. Its
default matches all four original demonstrations and both supplied gold queries.
The foreground is the minority of two colors. Extract four-connected components
and classify each using its own four-connected complementary regions: one
enclosed cavity means a frame; no cavity means a blob. Other foreground objects
do not block that cavity test.

For each axis, a selected frame contributes two singleton intervals at its
bounding-box endpoints. Each blob contributes its entire bounding-box span.
Merge overlapping intervals transitively, including endpoint contact. Sort the
groups and map them to `0, 2, 4, ...`. Draw thin rectangular frames between the
mapped endpoints and one foreground pixel per blob. The canvas includes a
one-cell halo around every blob. This preserves the exposed background row or
column beside exterior points in the original outputs.

| Setting | Components used to construct the compact layout |
| --- | --- |
| `frame_policy=all` | Every frame and blob; exact root reference program. |
| `frame_policy=outermost` | Frames outside every other frame's actual cavity, plus every blob. |

The alternative is an authored rule extension. Selection happens **before**
interval grouping, so deleting an inner frame also removes its coordinate
events. Deleting it only after rendering gives the wrong spacing. Stage A
classifies and selects input components; stage B consumes their kinds and bounds
to compute coordinates and draw the diagram. The Racket `layout-objects` binding
is the causal intervention point.

## Grammar and generation

Inputs are exact-list integer grids of dimensions `5..30`, with two distinct
colors in `0..9` and a strict background majority. There are `1..20` foreground
components, with at most one cavity per component. Selected frames must retain
distinct endpoint groups on both axes, and compact outputs must fit within
`30×30`. Tied palettes, multiple cavities, collapsed frames, and oversized
outputs are rejected. The implementation uses actual cavity containment for the
alternative; the sampler concentrates on nested or disjoint rounded contours.

The sampler varies the two colors, corner shapes, connected blob shapes,
reflections, and query transpositions. Its ten scene profiles include empty
frames, singleton and diagonal blobs, transitive interval chains, multiple
outer frames, three nesting levels, and exterior halos. Two `30×30` query
profiles contain substantial foreground structure. The original examples do not
uniquely settle every digital-topology or arbitrary-geometry extension; those
boundaries and the finite rival checks are reported explicitly.

Episodes support **2–6 demonstrations and 1–4 queries**. The first two scenes
teach column and row interval chains, three-level nested selection, empty frames,
diagonal separation, multiple outer frames, and leading as well as trailing
halos on both axes. Settings share the exact same input
streams for a seed. Local random streams avoid changing global random state.
The complete four-query bank is shuffled before prefix selection; increasing
either count preserves the existing prefixes. Returned grids own their rows.

## Run from the outer packet directory

Use Python 3.12+ with the packet dependencies and its freshly installed bundled
Racket runtime. Payload paths below resolve from `WORK/repo`.

```sh
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m pytest --import-mode=importlib generators/public_eval_2d0172a1/tests -q
PYTHONDONTWRITEBYTECODE=1 WORK/.venv/bin/python review.py run python3 -m arcpuzzles.review_public_creation preflight public_eval_2d0172a1 --root . --out ../checks/public_eval_2d0172a1/preflight
```

The native preflight executes all six original labels, then two demonstrations
and **four queries** for both settings at seeds `17` and `43`. Choose a new
output directory after source changes. For private authoring, load `adapter.py`
and call `generate(17, {"frame_policy": "outermost"}, demos=2, queries=4)`.
Keep its setting, answers, program, and future queries private. The retained
`WORK/checks/public_creation_tools.py` bridge creates protected causal evidence
and source-bound single-query public projections from the authoring preflight.

`sampler.py` exactly copies root `generator.py`, and `canonical.rkt` exactly
copies root `reference.rkt`. The adapter uses its adjacent declared resources.
These are authoring artifacts: source approval, registration, owner native
qualification, acceptance, and training admission remain separate.
