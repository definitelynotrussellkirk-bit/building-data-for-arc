# Parametric frame/shape assignment order

`shape_first` is the exact canonical source: loose shapes, in top-left order,
claim the tightest unused fitting frame. `frame_first` keeps the same parsing,
orientation preference, and centering, but processes frames in top-left order;
each frame takes the first unused fitting loose shape.

The family exposes 2–6 demonstrations and 1–4 independent queries. Inputs are
sampled without consulting the private setting. The first two demonstrations
contain assignment competition, required rotation, centering slack, and an
unmatched later shape. Query four is a substantive 30×30 boundary stress case.

Run focused checks from the packet root:

```sh
python3 review.py run python3 -m pytest generators/85e65da9fb15/tests/test_parameters.py -q
```
