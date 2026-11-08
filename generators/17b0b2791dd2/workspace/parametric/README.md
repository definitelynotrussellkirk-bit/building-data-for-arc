# Parametric exact-selector / nearest-target family

The default `target_policy=exact_vertical3` returns the selected canonical
Racket source byte-for-byte. The alternative `nearest_horizontal3` treats every
exact vertical triple as a selector, finds its nearest exact horizontal triple
by minimum cell-to-cell Manhattan distance (reading-order tie break), and paints
the union of those selected horizontal triples red.

The sampler supports 2–6 demonstrations and 1–4 queries independently. Inputs
are matched across settings; the four-query bank includes 14×16, 18×20, 24×26,
and substantive 30×30 scenes. Public helpers expose one query input per turn and
keep settings, programs, answers, future queries, and total-query hints private.

From the packet outer directory:

```bash
python3 review.py run python3 -m pytest \
  generators/17b0b2791dd2/tests/test_parametric_17b0b2791dd2.py -q
python3 review.py run python3 \
  generators/17b0b2791dd2/workspace/parametric/audit.py \
  --out ../checks/17b0b2791dd2/self-audit
python3 review.py run python3 -m arcpuzzles parametric qualify 17b0b2791dd2 \
  --out ../checks/17b0b2791dd2/qualification --summary
```

Passing evidence is finite and source-bound. It does not prove universal
identifiability, owner acceptance, or training admission.
