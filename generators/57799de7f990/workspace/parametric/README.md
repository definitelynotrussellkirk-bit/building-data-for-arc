# Parametric connection-axis rule — proposed prototype

This task-local prototype adds one **episode-level** rule parameter while leaving
`generator.py`, the selected canonical rule, and approval hashes unchanged.

| Parameter | Allowed values | Original/default |
| --- | --- | --- |
| `axis_mode` | `both`, `horizontal`, `vertical` | `both` |

The canonical setting, `both`, returns the exact canonical Racket program bytes.
`horizontal` disables only the vertical adjacency branch; `vertical` disables
only the horizontal adjacency branch. All settings still recognize a marker only
from four orthogonal color-2 arms, connect consecutive aligned centers through
zero cells, preserve the input, and paint connections with color 1. Thus object
roles, marker recognition, nearest-neighbor logic, and line drawing remain the
same; only the permitted connection direction changes.

`parameters(seed)` chooses the setting once and every demonstration and query in
that episode uses it. The retained seeds `0`, `1`, and `2` cover all settings.
Each episode contains three demonstrations and one query. Every retained input
has at least one visible horizontal and one visible vertical connection, so each
demonstration set distinguishes the chosen setting from both alternatives before
the query. Public challenge files contain demonstration labels and query inputs
only; parameter values, Racket text, rivals, and query answers stay in `private/`.

## Run from the outer extracted packet directory

```sh
python3 review.py run python3 generators/57799de7f990/workspace/parametric/prototype.py \
  --out ../checks/parametric/axis-mode-v1
python3 review.py run python3 -m pytest -q \
  generators/57799de7f990/tests/test_parametric_axis_mode.py
```

The materializer executes every saved label with the included Racket bridge. It
also replays all four canonical pairs with the exact default program, saves exact
Racket bytes and SHA-256 hashes for all three settings, builds one shared-input
three-way witness, checks both parameter rivals against every complete episode,
and writes a hash manifest.

## Scope and limits

This is a **proposed prototype**, not a production parametric API and not a
training or rule approval. Evidence is bounded to three deterministic episodes,
four controlled inputs per episode, and the two declared alternative settings.
The fixtures are lawful complete-diamond inputs but do not claim the full
production sampler distribution or universal identifiability against undeclared
rules.
