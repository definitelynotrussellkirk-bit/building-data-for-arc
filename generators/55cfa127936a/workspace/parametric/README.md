# Parametric family for `55cfa127936a`

`selection=topmost` is the byte-exact canonical rule. The alternative
`selection=singleton_anchor_nearest` first finds the row occupied by the unique
singleton yellow column, then keeps in every active column the yellow cell
nearest that row; distance ties keep the upper cell.

This is a real A-to-B dependency: **A** locates the singleton column and derives
its input-dependent row; the **intermediate** is that anchor row; **B** cannot
choose each column's retained yellow until that row is known.

Run the focused contract checks from the packet outer directory:

```sh
python3 review.py run python3 -m pytest -q \
  generators/55cfa127936a/tests/test_parametric_55cfa127936a.py
```

Qualify all declared settings on fresh seeds with four private queries:

```sh
python3 review.py run python3 -m arcpuzzles parametric qualify 55cfa127936a \
  --out ../checks/55cfa127936a/qualification --summary
```

The adapter supports 2–6 demonstrations and 1–4 queries. Inputs are independent
of the hidden setting, count-prefix stable, and the complete four-query bank
contains a substantive 30×30 case. `public_turn()` exposes only demonstrations
and one query input; settings, programs, answers, and future inputs remain
private.
