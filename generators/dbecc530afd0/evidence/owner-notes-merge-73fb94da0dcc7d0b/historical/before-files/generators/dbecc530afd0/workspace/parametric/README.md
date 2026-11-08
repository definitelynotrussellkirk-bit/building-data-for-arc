# `dbecc530afd0` inset-depth prototype

This directory is an isolated review prototype. It does **not** change the
production generator or canonical rule. The episode parameter is chosen once:

- `inset_depth=1` — the exact canonical Racket program, byte for byte.
- `inset_depth=2` — the same rectangle detector and composition logic, but only
  cells at least two steps inside every rectangle are painted red.

All retained episode labels and counterfactual labels are executed through the
bundled Racket bridge. Inputs are shared across settings, contain one or two
complete corner-disjoint rectangles of at least 5x5, and every input visibly
distinguishes the two settings. Public files contain only three labeled
training pairs and one unlabeled query input; private files retain settings,
programs, labels, and rotation analysis.

From `WORK/`, build immutable evidence with:

```bash
python3 run_with_racket.py \
  python3 generators/dbecc530afd0/workspace/parametric/prototype.py \
  --seed 0 \
  --out ../checks/parametric/inset-depth-v1
```

The command refuses to overwrite an existing directory.
