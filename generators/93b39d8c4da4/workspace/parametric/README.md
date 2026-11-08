# Parametric template-transform family — `93b39d8c4da4`

The private episode parameter `template_transform` has three settings:

- `identity` — byte-exact canonical rule;
- `mirror_lr` — mirror the tight-normalized input template left/right;
- `rotate_cw` — rotate the tight-normalized input template clockwise.

For every setting, step A extracts the complete connected color-2 template and
tight-normalizes its occupied-cell geometry. The intermediate is that exact
input-dependent geometry after the episode-fixed transform. Step B stamps the
intermediate in color 8 at every visible color-3 marker on a fresh blank canvas.
A fixed-L wrong-intermediate program changes the final protected-Racket output.

Inputs are matched across settings. Requests support 2–6 demonstrations and
1–4 queries independently. The four query canvases are 30×30, 24×30, 30×24 and
27×29. Every scene uses an asymmetric 3×3 connected template with dihedral orbit
8, at least six markers, boundary coverage and a genuine overlapping-stamp pair.
The first-turn projection reveals all demonstrations plus one input-only query,
omitting the program, setting, future inputs and every query answer.

`audit.py` fits the other settings and four executable shortcut classes using
only demonstrations, then inspects queries only for survivors. This bounded
review is finite evidence, not a proof of universal uniqueness or training value.
