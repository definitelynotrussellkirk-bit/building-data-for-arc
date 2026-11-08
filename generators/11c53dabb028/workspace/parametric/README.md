# Native component-frame and repeat-count family

The native adapter retains all four existing repeat-count programs and adds an
episode-fixed `input_frame` parameter. Its eight settings are the Cartesian
product of `input_frame=input|largest_component`, `vertical_repeats=1|2`, and
`horizontal_repeats=1|2`. The default `(input,2,2)` is the exact canonical source.
The approved production generator and canonical authority remain unchanged.

With `input`, the retained prototype selects the first row-major nonzero color,
inverts the zero/nonzero mask, and periodically tiles it. With `largest_component`,
first find the four-connected nonzero component with the most occupied cells,
ignoring color boundaries. Ties choose the component whose first actual occupied
cell is earliest in row-major order. Isolate that component while preserving its
colors, clear every other component, then crop its bounding box. Run the retained
color selection, mask inversion, and tiling on that intermediate grid.

This is a causal composition: the selected component determines the later color,
mask, height, and width. Cropping the original bounding box leaves foreign pixels
inside the frame and gives different answers, including on equal-size30x30 outputs.
Binary masks are used only to discover membership; original colors are retained.

## Grammar and implementation

Original inputs are exact-list rectangular integer0..9 grids with sides1..15,
containing at least one zero and one nonzero cell. The intermediate can be solid;
its negative tile is then all zero. `prototype.solve` keeps its previous input
validation and delegates to the extracted `prototype.tile_output` kernel. The
native adapter uses that same kernel for derived frames, and reuses every retained
`program_for` Racket rule. It does not fork the original tile semantics.

The shared input bound keeps every repeat setting inside ARC's30x30 output limit.
A30x30 original input would produce60x60 under the canonical2x2 setting, so it is
outside this family. The retained15x15 stress inputs produce substantive30x30
outputs; their largest component spans the full input and surrounds isolated
clutter, making component isolation observable without changing output dimensions.

`sampler.py` constructs complete six-demo/four-query banks with separate local
SHA-derived palette, geometry, painting and presentation streams. Inputs are
matched across all eight settings. Supported counts are3..6 demos and1..4 queries,
with exact integer seeds0..2**63-1. The complete query bank is shuffled before
taking a prefix; changing demo count leaves queries unchanged.

Three mandatory demonstrations cover pixel-count selection versus bounding-box
area, multicolor four-connectivity, an interior distractor, same-row ties whose
bounding-box corners order differently from actual first cells, frequency/rank
color shortcuts, and the retained left-edge-last scan defect. The last example
places different colors at columns0 and1 of the first occupied row in both frames.
Queries cover1x2,9x13,13x11 and15x15. The tiny component frame is a valid solid1x1
intermediate. No additional demonstrations were needed.

## Native verification and replay

From the packet outer folder, using its configured interpreter:

```sh
WORK/.venv/bin/python review.py run python3 -m pytest --import-mode=importlib \
  generators/11c53dabb028/tests/test_native_family.py \
  generators/11c53dabb028/tests/test_native_sampler.py \
  generators/11c53dabb028/tests/test_native_adapter.py \
  generators/11c53dabb028/tests/test_parametric_repeat_counts.py -q
WORK/.venv/bin/python review.py run python3 \
  generators/11c53dabb028/workspace/parametric/audit.py --out ../checks/component-tile-fresh
WORK/.venv/bin/python review.py run python3 -m arcpuzzles parametric qualify \
  11c53dabb028 --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/component-tile-qualification-fresh --summary
```

The native adapter emits deterministic Python claims; qualification and the
private audit execute Racket independently. The current evidence inventory is
`evidence/manifest.json`. The return retains72passing focused tests including the
eight original prototype tests;392core rival comparisons (384demo-refuted,
8finite-consistent);80additional independently defined comparisons (56refuted,
24consistent); and80maximum-count/max-seed protected labels. No surviving rival
changed a query answer. Consistent cases are controls that are inactive for the
setting: unit-repeat scaling/reflection or component selection under `input`.

Native qualification, causal replay and public-projection records are under
`checks/11c53dabb028/`. Public preview files contain the demos and exactly one
query input; the whole bundle and directory listing stay controller-only.
Private mappings preserve the shuffled query input/answer pairs and allow early
stop with identical first-turn bytes. Finite checks grant neither owner
acceptance, universal identifiability nor training admission.

## Retained repeat-only prototype and historical evidence

The original prototype CLI and verifier below remain available for their
repeat-only API. Their reported measurements predate this native extension and
must not be presented as fresh native qualification. The old inventory is
preserved in the return at `checks/11c53dabb028/retained-prototype-manifest.json`.

### Proposed repeat-count rule prototype

This task-local prototype does **not** change the selected production generator,
the canonical Racket authority, its approval, or training admission. It varies
two hidden episode-level rule parameters while preserving the original family:
select the first row-major nonzero color, invert the zero/nonzero mask, and tile
the resulting periodic pattern.

| Parameter | Allowed values | Canonical/default | Effect |
|---|---|---|---|
| `vertical_repeats` | exact integer `1` or `2` | `2` | output height is `vertical_repeats × input height` |
| `horizontal_repeats` | exact integer `1` or `2` | `2` | output width is `horizontal_repeats × input width` |

The setting is selected once per complete episode and remains fixed across all
three demonstrations and four queries. The existing lawful input domain is
unchanged: each side is `1..15`, area is at least two, and the grid contains at
least one zero and one nonzero cell. Restricting repeat counts to `{1,2}` keeps
every output within `30×30` without narrowing that input domain. The `(2,2)`
program is byte-identical to the canonical rule; the other three programs only
change the two output-size multipliers.

## Exact replay

From the outer packet extraction directory, materialize one answer-masked public
challenge with exactly four queries:

```bash
python3 review.py run python3 \
  generators/11c53dabb028/workspace/parametric/prototype.py \
  --seed 17 --vertical-repeats 2 --horizontal-repeats 1 \
  --train 3 --test 4 --public \
  --out ../checks/parametric/11c53dabb028-repeat-count-v1/public-example.json
```

Run the complete exact-Racket verification and retain private/public artifacts:

```bash
python3 review.py run python3 \
  generators/11c53dabb028/workspace/parametric/verify.py \
  --seed-base 20261023 \
  --artifact-dir ../checks/parametric/11c53dabb028-repeat-count-v1/artifacts \
  --out ../checks/parametric/11c53dabb028-repeat-count-v1/report.json
```

Run focused tests:

```bash
python3 review.py run python3 -m pytest -q \
  generators/11c53dabb028/tests/test_parametric_repeat_counts.py
```

The verifier covers one retained episode for each of the four settings: 28
Racket-labeled pairs, 84 pair-level alternative-setting checks, 48 query-rival
checks using only the demonstrations, all four canonical pairs, and 12 boundary
checks spanning `1×15`, `15×1`, and `15×15` inputs. Public challenge filenames
are opaque SHA-256 IDs derived only from visible demonstrations and query inputs;
private settings, seeds, programs, metadata, and query answers cannot affect the
public bytes or names.

This is bounded authoring evidence for four settings and four retained seeds.
Its declared rivals are only the other three repeat-count settings; it is not a
claim of identifiability against arbitrary programs or approval of a production
parametric API.
