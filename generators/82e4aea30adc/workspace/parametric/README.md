# Episode-level interior-area threshold prototype

This is a task-local prototype, not a production generator API.

It promotes one rule constant to an episode parameter:

- `gray_max_interior_area=1` — the unchanged canonical rule: only a one-cell interior becomes gray (5).
- `gray_max_interior_area=2` — interiors of area one or two become gray; larger interiors remain orange (7).

The parameter is selected once per episode. Each episode has three labeled demonstrations and one masked query. Every input contains lawful frames with interior areas `1`, `2`, and `>2`, so each demonstration and query distinguishes the two settings. All labels and rival outputs are produced by the included Racket bridge from the instantiated Racket program; the default program is byte-for-byte canonical.

Run the focused tests:

```bash
python3 review.py run python3 -m pytest -q generators/82e4aea30adc/tests/test_parametric_threshold.py
```

Materialize retained public/private evidence:

```bash
python3 review.py run python3 generators/82e4aea30adc/workspace/parametric/prototype.py \
  --out ../checks/parametric/gallery
```
