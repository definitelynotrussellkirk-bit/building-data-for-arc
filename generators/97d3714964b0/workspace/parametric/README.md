# Native largest-hollow threshold family

`solid_policy` has two values:

- `independent` (byte-exact canonical): every hollow color-7 component becomes
  4 and every solid color-7 component becomes 2.
- `largest_hollow_threshold`: first compute the largest hollow component's
  bounding-box area, then recolor only solids at least that area to 2; smaller
  solids remain 7. Hollows still become 4.

Every generated input contains two hollow frames and two solid rectangles. One
solid matches the largest hollow's dimensions while a second solid is smaller,
so every demonstration visibly separates the two policies. Inputs are matched
across settings, count-prefix-stable, and the fourth query is a substantive
30×30 stress case.

```bash
python3 review.py run pytest -q \
  generators/97d3714964b0/tests/test_parametric_native_adapter.py
python3 review.py run python3 -m arcpuzzles parametric qualify 97d3714964b0 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/97d3714964b0/qualification --summary
```
