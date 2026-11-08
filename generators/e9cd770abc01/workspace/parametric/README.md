# `e9cd770abc01` parametric authoring family

This prototype preserves the exact canonical default and adds one nearby causal setting:

- `paint_scope=nearest_only` — select the color-3 component whose bounding-box center is Manhattan-nearest the grid center, with bbox lexicographic tie-breaking, and repaint only that object color 7.
- `paint_scope=nearest_size_class` — perform the same selection, bind the selected object's occupied-cell count, and repaint every color-3 component with that count color 7.

The alternative is sequential: step A determines an input-dependent target object; its occupied size is the intermediate consumed by step B. The first two constructive demonstrations reject 14 declared alternatives, including Euclidean/centroid selection, nearest occupied cell, first/last/smallest/largest object, paint-all, fixed size, bbox-area/dimensions class, exact shape class, and one-sided size thresholds.

A second adversarial pass also retained two selectors that are observationally equivalent on the teaching pair—centroid Manhattan and bbox-edge distance—as **shadow selectors** rather than falsely claiming the demonstrations distinguish them. The probe requires every demo-equivalent shadow selector to agree with the intended rule on all four generated queries for every audited seed, setting, and demonstration count; any query disagreement is a hard failure. This follows the packet rule that an alternative changing no query answer is not an ambiguity.

Reproduction from the packet root:

```bash
python review.py run python3 -m pytest -q --import-mode=importlib \
  generators/e9cd770abc01/tests/test_parametric_e9cd770abc01.py
python review.py run python3 generators/e9cd770abc01/workspace/parametric/probe.py \
  --out generators/e9cd770abc01/workspace/parametric/evidence/current/study.json
python review.py run python3 -m arcpuzzles.review_programs \
  generators/e9cd770abc01/workspace/parametric/canonical.rkt
python review.py run python3 -m arcpuzzles.review_programs \
  generators/e9cd770abc01/workspace/parametric/size_class.rkt
```

The default probe runs 70 deterministic jobs over seven seeds, both settings, demonstration counts 2–6, and four queries. It checks deterministic labels, sampler invariants, matched setting inputs, the 14-rival bank, both shadow selectors, and a content-bearing 30×30 query. The retained authoring preflight independently executes labels in protected Racket. Neither artifact claims owner acceptance or training admission.
