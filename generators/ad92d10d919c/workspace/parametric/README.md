# Parametric diagonal-match threshold — proposed prototype

This task-local prototype varies one episode-level rule parameter:

| Parameter | Allowed values | Original/default |
| --- | --- | --- |
| `required_matches` | `3`, `4` | `4` |

`4` returns the selected canonical Racket program byte-for-byte. `3` changes the
predicate so a zero center fills when any nonzero color occupies at least three
of its four diagonal neighbors. The rule choice is made once per episode and is
used unchanged for all three demonstrations and the query.

Every retained input contains a complete same-color X, a three-corner same-color
X, and a mixed 2+2 four-corner control. Thus every demonstration distinguishes
threshold 3 from threshold 4, while the mixed control continues to teach color
agreement. Labels and declared-rival outputs are produced by executing the exact
materialized Racket text with the included bridge; no Python label mirror is used.

Run from the outer extracted packet directory:

```sh
python3 review.py run python3 generators/ad92d10d919c/workspace/parametric/prototype.py \
  --out ../checks/parametric/gallery
python3 review.py run python3 -m pytest -q \
  generators/ad92d10d919c/tests/test_parametric_threshold.py
```

The gallery writes two complete private episodes, masked public challenges,
exact `.rkt` programs and hashes, a shared-input differing witness, runtime
identity, source hashes, and a report. This is a **proposed prototype**, separate
from the repaired fixed-rule production generator.

Limits: only two threshold settings, two retained seeds, controlled fixtures,
one query per episode, and only the declared parameter rival. It is finite
execution evidence, not production approval or a proof over all inputs/seeds.
