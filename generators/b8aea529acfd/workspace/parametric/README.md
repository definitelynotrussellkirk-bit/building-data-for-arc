# Reflection-policy parametric family

This proposed family keeps the accepted `b8aea529acfd` grammar and its exact
canonical default, while making the post-crop reflection an episode-fixed
parameter:

- `left_right`: crop, then flip left-to-right (the exact canonical program)
- `top_bottom`: crop, then flip top-to-bottom
- `long_dimension`: crop, measure the cropped body, then flip along its long dimension
- `short_dimension`: crop, measure the cropped body, then flip along its short dimension

The first two demonstrations deliberately disagree in **canvas** aspect and
**cropped-body** aspect.  Therefore a solver must use the crop-derived
intermediate instead of treating outer dimensions as a shortcut.  Every
episode has 2–6 demonstrations and exactly four novel queries; two query
canvases are 30×30.

Generate a private labeled episode:

```bash
python generators/b8aea529acfd/workspace/parametric/prototype.py \
  --seed 17 --policy long_dimension --demos 3 --queries 4
```

Generate only the public sequential payload:

```bash
python generators/b8aea529acfd/workspace/parametric/prototype.py \
  --seed 17 --policy long_dimension --public
```

Native qualification is performed through the repository CLI, which executes
all labels with the protected Racket runtime rather than trusting the Python
mirror.
