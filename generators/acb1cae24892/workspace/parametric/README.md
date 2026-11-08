# acb1cae24892 parametric family

`outline_only` is the exact selected canonical source. `fill_largest_hole`
first constructs all canonical rectangle outlines. Those outlines create closed
zero regions; the second stage finds the largest newly enclosed region and fills
it with its surrounding outline color. The protected counterfactual chooses the
smallest region instead.

Focused run:

```bash
python3 review.py run python3 -m pytest -q \
  generators/acb1cae24892/tests/test_generator_acb1cae24892.py \
  generators/acb1cae24892/tests/test_parametric_outline_hole_fill.py
```
