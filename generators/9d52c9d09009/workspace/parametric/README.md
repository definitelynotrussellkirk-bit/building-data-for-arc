# Parametric four-region output color — proposed prototype

This task-local prototype varies one episode-level rule parameter while keeping
the original object roles and reasoning path unchanged:

| Parameter | Allowed values | Original/default |
| --- | --- | --- |
| `four_region_color` | `4`, `7` | `7` |

The rule still finds each 4-connected color-8 object, counts 4-connected zero
regions inside its bounding box, and recolors the object by the count. Only the
exception for four regions varies: the canonical setting maps `4 → 7`; the
alternative maps `4 → 4`. Setting `7` returns the selected canonical Racket
program byte-for-byte. Setting `4` makes one exact `map-color` substitution.

The parameter is selected once per episode and held fixed across three
illustrated demonstrations and one query. Every retained input uses the repaired
production generator's `all_counts` profile, so it contains a four-region object;
therefore every demonstration distinguishes the two settings. The exact
instantiated Racket text, not a Python mirror, produces both selected labels and
rival outputs. Public challenge files omit the parameter, Racket program, and
query answer.

Run from the outer extracted packet directory:

```sh
python3 review.py run python3 generators/9d52c9d09009/workspace/parametric/prototype.py \
  --out ../checks/parametric/four-region-color
python3 review.py run python3 -m pytest -q \
  generators/9d52c9d09009/tests/test_parametric_four_region_color.py
```

The gallery contains two complete private episodes, two masked public
challenges, exact `.rkt` programs, a shared-input witness with both outputs,
runtime identity, source hashes, and a report. This is a **proposed prototype**
only. The selected production path remains fixed to canonical color 7.

Limits: two parameter settings, two retained episode seeds, controlled generated
`all_counts` fixtures, three demonstrations, one query, and only the declared
parameter rival. These executions do not establish approval, universal
identifiability, or coverage of every seed and rival.
