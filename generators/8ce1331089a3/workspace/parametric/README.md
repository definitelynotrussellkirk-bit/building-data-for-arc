# Parametric route-action family

`path_rule=wall_endpoint` is the exact canonical rule. Matching interior colors
move to the adjacent inner wall and non-border distractors disappear.

`path_rule=dominant_trace` adds one composed dependency without changing the
input grammar:

1. Count matching interior pixels for the top, bottom, left, and right border
   colors and select the unique most frequent route.
2. Move every matching pixel toward its color-defined wall, but draw the full
   source-to-wall path only for pixels on the selected route. Other routes keep
   the canonical wall endpoint.

Thus the second operation cannot select which paths to expand until the first
operation has produced the input-dependent dominant route. Generated episodes
use the same inputs across settings, 2–6 demonstrations, 1–4 queries, unique
inputs, changing dominant directions, non-border distractors, and a substantive
30×30 fourth query. `public_turn()` exposes one current query and no settings,
program, query answer, future input, or total-query hint.

Focused checks from the packet root:

```bash
python3 review.py run python3 -m pytest \
  generators/8ce1331089a3/tests/test_parametric.py -q
python3 review.py run python3 \
  generators/8ce1331089a3/workspace/parametric/audit.py \
  --out ../checks/8ce1331089a3/self-audit
python3 review.py run python3 -m arcpuzzles parametric qualify 8ce1331089a3 \
  --seed 0 --seed 17 --demos 3 --queries 4 \
  --out ../checks/8ce1331089a3/qualification --summary
```

The finite audit covers seven plausible rivals on two seeds at the minimum
supported demonstration count. It does not prove universal identifiability or
admit any data to training.
