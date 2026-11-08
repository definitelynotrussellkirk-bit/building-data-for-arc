# Proposed threshold parameter prototype

This isolated prototype keeps the original task's reasoning structure and varies
one hidden episode-level parameter: the fixed blue-count threshold is 3, 4, or
5. Threshold 4 is the canonical/default behavior. The selected production
generator and canonical authority are not changed by this prototype.

From the outer extraction directory, materialize all three complete episodes,
execute every retained rule with the included Racket bridge, compare against the
independent Python mirror, test both alternative thresholds on every pair, and
write public challenges with hidden parameters and query answers removed:

```bash
python3 review.py run python3 generators/2c48ea6caa2e/workspace/parametric/prototype.py \
  --out ../checks/parametric/evidence.json \
  --write-public ../checks/parametric/public \
  --seed-start 26000
```

Retained exact programs are under `rules/`. The focused test is
`generators/2c48ea6caa2e/tests/test_parametric_prototype.py`.
