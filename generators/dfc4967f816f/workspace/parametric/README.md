# Proposed parametric rule: symmetry output color

This task-local prototype keeps the vertical-symmetry decision unchanged and
chooses one hidden episode-level `output_color`: `8` is byte-for-byte canonical;
`4` is the proposed alternative. Input sampling is independent of the setting.
The prototype supports 2–6 demonstrations and 1–8 queries independently; the
review evidence uses three demonstrations and four distinct queries.

The four-query schedule covers 3, 4, 5, and 6 tiles (widths 11, 15, 19, and 23).
The original one-row 3×3-tile grammar cannot produce an exact 30×30 input without
changing the task, so 3×23 is the recorded lawful maximum.

From the outer packet directory:

```bash
python3 review.py run python3 generators/dfc4967f816f/workspace/parametric/prototype.py \
  --out ../checks/parametric/dfc4967f816f --seeds 0 1 --demos 3 --queries 4
```

Public files are named only by the hash of visible demonstrations and query
inputs. Hidden settings, exact Racket programs, query answers, and setting maps
stay under the private/rules evidence paths. `adapter.py` and `promotion.json`
prepare, but do not approve, the family for native qualification.
