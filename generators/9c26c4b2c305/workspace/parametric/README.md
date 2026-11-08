# Alignment-policy parametric prototype

This task-local family keeps the reviewed two-panel grammar and varies only how
the bottom panel is aligned before the green occupancy OR:

- `aligned` is the exact canonical Racket program.
- `reflect_bottom` horizontally reflects the bottom panel.
- `top_heavier_reflect_bottom` first counts occupied cells in both panels and
  reflects only when the top count is greater than the bottom count.

The first two demonstrations deliberately exercise opposite count branches, so
all three declared programs are distinguishable from demonstrations alone.
Inputs are matched across settings. The first four queries include widths
18, 21, 27, and 30; a 30×30 input is not lawful because the reviewed grammar
has a fixed height of nine rows.

Run the focused suite through the packet launcher:

```bash
python3 review.py run python3 -m pytest \
  generators/9c26c4b2c305/tests/test_parametric_alignment_policy.py -q
```
