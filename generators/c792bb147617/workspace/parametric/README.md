# Proposed palette-rotation parameterization

Status: **proposed prototype**, separate from the approved canonical generator.
It does not change `generator.py`, the canonical authority, production sampling,
approval, catalog selection, exports, or training admission.

## Rule parameter

The episode-fixed `orientation` parameter rotates the canonical four-color
compass around every original blue(1) anchor. Inputs, row-major anchor order,
in-bounds clipping, input preservation, and the four cardinal writes remain the
same.

| orientation | up | left | right | down |
|---|---:|---:|---:|---:|
| `canonical` | 2 | 7 | 6 | 8 |
| `rotate_cw` | 7 | 8 | 2 | 6 |
| `rotate_180` | 8 | 6 | 7 | 2 |
| `rotate_ccw` | 6 | 2 | 8 | 7 |

`canonical` returns the selected canonical `program_solution` byte-for-byte.
Alternative programs change only the four directional color literals. The
parameter changes the executed transformation rather than input appearance.

## Episode construction

`generate_episode(seed, orientation, demos, queries)` supports 2..8
demonstrations and 1..8 queries independently. A 16-profile schedule supplies
unique dimension pairs, exact generator overrides, an interior first
demonstration, and a boundary/count-eight second demonstration. The private
setting never enters input sampling, so the same seed and counts produce the
same ordered inputs for all four orientations. The first interior example shows
all four directional assignments, making every chosen orientation the sole
survivor among the four declared settings from demonstrations alone.

The prototype reuses the reviewed canonical generator through an exact adjacent
source path. Python outputs are claims for authoring tests; native qualification
re-executes every label and every declared rival through protected Racket.

## Exact runnable commands

From the outer packet directory containing `review.py`:

```bash
python3 review.py run python3 -m pytest \
  generators/c792bb147617/tests/test_parametric_palette_rotation.py -q

python3 review.py run python3 -m arcpuzzles.cli parametric manifest c792bb147617 \
  --evidence generators/c792bb147617/workspace/parametric/evidence/current \
  --include generators/c792bb147617/tests/test_parametric_palette_rotation.py \
  --reported-checks 'Focused tests cover exact canonical bytes, four mappings, matched inputs, distinct 8+8 counts, clipping, overlap order, validation, and demo-only finite-rival identification.'

python3 review.py run python3 -m arcpuzzles.cli parametric qualify c792bb147617 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/parametric/qualification
```

The qualification command covers all four settings, both seeds, three
demonstrations, and four distinct queries per episode. It is qualification
evidence only; owner acceptance remains a separate explicit action.

## Limits

The parameter family contains only four compass rotations. It does not vary the
anchor color, active directions, write order, number of writes, or input grammar.
The input schedule stays within the canonical generator's 6..16 dimensions,
2..8 non-cardinally-adjacent anchors, and `edge_mode=none|some` domain. Finite
settings/seeds and declared-rival checks do not prove uniqueness against every
imaginable rule or measured learning benefit. No variant is approved or admitted
to training by these files or by a successful qualification run.
