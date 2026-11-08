# Parametric prototype: output bar color

This prototype keeps the original row-wise reasoning unchanged: count non-7
cells, locate the color-6 anchor by rank, and reconstruct a contiguous bar at
the corresponding offset. The episode parameter changes only the bar's output
color.

- `bar_color=8` is the exact canonical Racket source, byte-for-byte.
- `bar_color=3` changes only the single bar-paint literal.
- One value is chosen once per episode by seed parity.
- Each episode has three labeled demonstrations and one unlabeled query.
- Labels and counterfactuals are executed through the real Racket bridge.
- All query rotations are checked against the other parameter setting.

Run from `WORK/` after `python3 setup_racket.py`:

```bash
python3 run_with_racket.py python3 \
  generators/587396c0817d/workspace/parametric/prototype.py \
  --seed 0 --out ../checks/parametric-bar-color
```

The prototype is evidence only. It does not modify the selected canonical rule,
add a production axis, or establish identifiability against undeclared rivals.
