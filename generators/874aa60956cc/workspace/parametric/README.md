# Bounding-border touch-count relay

This native proposal preserves the exact canonical rule as `border_mode=all`
and adds `border_mode=touch_count_relay` on matched input grids.

## Sequential dependency

1. **A:** find the first color that occurs exactly twice and paint its
   axis-aligned bounding border.
2. **Intermediate:** count the distinct later exactly-twice colors having at
   least one original clue on that derived controller border; the sampler
   constructs values 1, 2, and 3.
3. **B:** order the three later paired colors by first row-major appearance,
   select rank equal to the count, and paint that color's bounding border over
   A's result.

B cannot be selected before A supplies its input-dependent border and touch
count. `wrong_intermediate.rkt` forces rank 1; the retained 30×30 witness has
actual count 3 and a different final output.

The sampler supports 2–6 demonstrations and 1–4 queries independently. Inputs
are deterministic per split/index, prefix-stable, and identical between the two
settings. Every scene contains one controller pair, three candidate pairs, a
singleton, and a triple. The first two demonstrations constructively reject the
canonical all-pairs rule and the declared fixed-count, touched-cell-count,
last-touched, completion-order, numeric-order, controller-only, and skip-A
shortcuts. Queries include an 8×9 minimum profile and a substantive 30×30
boundary-spanning profile.

`public_turn` exposes all labeled demonstrations and exactly one current query
input. It omits settings, programs, query answers, future query inputs, query
indices, and total-count hints; the first turn is byte-identical under one-query
and four-query requests.

From the packet outer directory:

```bash
python3 review.py run python3 -m pytest -q \
  generators/874aa60956cc/tests/test_parametric_touch_relay.py
python3 review.py run python3 \
  generators/874aa60956cc/workspace/parametric/audit.py \
  --seed 19 --out ../checks/874aa60956cc/self-audit
python3 review.py run python3 -m arcpuzzles parametric qualify 874aa60956cc \
  --out ../checks/874aa60956cc/qualification --summary
```

The adapter and evidence are a reviewer candidate. Exact-source owner acceptance
and any training admission remain pending.
