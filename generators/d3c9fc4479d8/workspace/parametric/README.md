# Legend rewrite mode: once or cascade

**Status: proposed task-local prototype.** The selected production generator and
canonical authority are unchanged. This family keeps the original top-row legend,
body recoloring, row removal, and unmapped-color preservation, while choosing one
private episode-fixed rule parameter:

| `mode` | Behavior |
| --- | --- |
| `once` | Apply each source→target mapping once to the original body cell (the exact canonical program). |
| `cascade` | Repeatedly follow the legend chain until the color is no longer a source; cycles stop at the first repeated color. |

Every sampled input includes an acyclic chain `a→b→c`, a disjoint mapping, and
preserved control colors. The same inputs are used for both modes. Demonstrations
alternate legends beginning at columns 0 and 1 so a fixed-origin parser cannot
survive the minimum two-example lesson. The finite certificate fits eight declared
rivals using demonstrations only; it does not claim universal uniqueness.

The adapter supports 2–6 demonstrations and 1–4 queries independently. Ordinary
retained episodes use four distinct query shapes: 10×12, 16×20, 24×24, and 30×30.
The large cases contain dense body content across the canvas rather than padded
small scenes. `first_turn()` reveals the demonstrations and only query 1, with no
future-query or total-count metadata; its content matches a one-query request.

Run from the packet root:

```bash
python3 review.py run python3 \
  generators/d3c9fc4479d8/workspace/parametric/prototype.py build \
  --seed 17 --demos 3 --queries 4 --mode all \
  --out ../checks/d3c9-parametric-examples

python3 review.py run python3 \
  generators/d3c9fc4479d8/workspace/parametric/prototype.py verify \
  ../checks/d3c9-parametric-examples

python3 review.py run python3 \
  generators/d3c9fc4479d8/workspace/parametric/probe.py \
  --out ../checks/d3c9-parametric-probe.json

python3 review.py run python3 -m pytest -q \
  generators/d3c9fc4479d8/tests/test_parametric_rewrite_mode.py
```

Public files are named by `reviewer_support.public_challenge_id` over exact visible
bytes. Seeds, settings, reference programs, query answers, source bindings, Racket
runtime identity, and certificates remain private. The verifier refuses unexpected
paths, malformed grids, stale source/runtime/program claims, duplicate inputs, and
labels that do not replay through both protected Racket programs. Qualification or
owner acceptance remains separate; nothing here admits data to training.
