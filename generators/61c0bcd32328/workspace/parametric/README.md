# Native corner-copy direction family

This task-local family preserves the exact canonical corner-copy rule as its
default and varies one hidden episode-fixed parameter:

- `direction=clockwise` — exact canonical Racket bytes.
- `direction=counterclockwise` — the same component extraction, corner
  classification, source preservation, and translation, but to the other
  adjacent corner.

`adapter.py` is the native promotion entry point and loads `native.py` by exact
adjacent path. The input stream is independent of the selected direction and
supports 2–6 demonstrations plus 1–4 private queries with stable prefixes. The
first two demonstrations constructively cover all four corner classes,
singleton objects, non-rectangular geometry, multiple corner objects, and a
same-color diagonal decoy. Four queries are retained controller-side; the fourth
is a dense 30×30 boundary case. `public_turn(...)` exposes one query at a time
without settings, programs, answers, future inputs, or a total-query hint.

The sequential dependency is native to the rule:

1. Segment same-color 4-connected components and classify each component from
   its input-derived bounding-box corner.
2. Use that intermediate corner label and the episode direction to choose the
   translation formula and paint the copied cells.

`self_audit.py` checks matched inputs, count-prefix stability, public projection,
30×30 content, and eight finite plausible rivals. It also executes both the
qualified rule and a wrong-corner-intermediate counterfactual through protected
Racket.

From the packet root:

```bash
python3 review.py run python3 -m pytest -q \
  generators/61c0bcd32328/tests/test_parametric_native.py

python3 review.py run python3 \
  generators/61c0bcd32328/workspace/parametric/self_audit.py \
  --out ../checks/61c0bcd32328/self-audit --stress-seeds 64

python3 review.py run python3 -m arcpuzzles parametric qualify 61c0bcd32328 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/61c0bcd32328/qualification --summary
```

Qualification and reviewer evidence do not constitute owner acceptance or
training admission.
