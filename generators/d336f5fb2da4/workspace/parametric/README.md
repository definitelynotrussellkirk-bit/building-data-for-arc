# Proposed control-6 handedness family

Parameter: `magenta_rotation = cw | ccw`. `cw` is the selected canonical rule byte-for-byte. The alternate changes only the interpretation of control color 6; identity color 4, row reflection color 7, source normalization, vector following, and clipping behavior stay invariant.

The first two demonstrations are asymmetric control-6 witnesses. Input sampling is setting-independent, supports 2–6 demonstrations and 1–4 distinct queries, and the fourth query is a substantive 30×30 diagonal case. `visible_turn()` exposes exactly one current query with no private setting, answer, seed, ordinal, or total-count hint.

From the packet root:

```bash
python3 review.py run python3 -m pytest -q generators/d336f5fb2da4/tests
python3 review.py run python3 generators/d336f5fb2da4/workspace/parametric/verify.py --out ../checks/parametric/d336f5fb2da4
```

This is a proposed task-local family, not accepted parametric data and not training-admitted.
