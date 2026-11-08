# Complete-window participation

First detect every complete all-gray square in the original scene. Count how
many of those windows contain each cell, then recolor cells reaching the chosen
minimum to blue. Changing the scene while detecting windows gives a different
answer: the included scan-and-paint counterfactual demonstrates that dependency.

| Parameter | Values |
|---|---|
| `window_size` | 2 or 3 cells per side |
| `minimum_overlap` | at least 1 or 2 complete windows per cell |

The `(2,1)` default returns the exact canonical Racket bytes. Every other setting
has its own executable Racket program. Parameters stay fixed per episode.
Inputs match across settings. Independent demo/query streams support2–6demos
and1–4queries; normal requests use2demos and4queries. Queries have12×14,
18×20,24×29and30×30 canvases in a seed-dependent order, so size does not encode
a fixed query position. That order is independent of requested counts and
settings, preserving query prefixes. The large scene contains25distributed shapes;
it is not a small scene padded with empty border.

Both mandatory demonstrations contain overlapping-window positives, a positive
rectangle with an ineligible tail, unequal overlapping rectangular cores, and
large T/ring negatives. The smaller core contributes eligible cells outside the
largest rectangle, so a largest-core shortcut cannot fit the demonstrations. Additional scenes
vary placement, orientation, holes, rectangle dimensions and connected walks.
The teaching check uses only demonstrations, distinguishes all4settings and
rejects7named rivals, including the retained component-size shortcut and both
maximum-rectangle alternatives found in independent review. These are
bounded checks, not a claim of uniqueness among arbitrary possible rules.

The prototype grammar is richer than the unchanged production sampler. Its
canonical coverage audit remains open; native parameter acceptance is a separate
source-bound decision, and neither step admits model trajectories to training.

From the library root:

```bash
PYTHONPATH=src:shared/runtime .venv/bin/python -m pytest -q \
  generators/6237039401ed/tests/test_parameters.py
PYTHONPATH=src:shared/runtime .venv/bin/python \
  generators/6237039401ed/workspace/parametric/audit.py --out var/window-audit.json

# After native qualification and acceptance, reuse the shared checked exporter:
arcpuzzles export --parametric-only --id 6237039401ed --count 4 --seed 17 \
  --style grids --render chatml --out var/datasets/windows-s17
arcpuzzles inspect-export var/datasets/windows-s17
```

Set `RACKET_PATH` to the verified bundled runtime when Racket is not on PATH.
The export has four supervised rows per episode. Give the model each row's
`messages` prompt and current answer target separately; keep query indices,
future inputs, total query count, settings, seeds and private provenance with
the controller.
