# Task-local review tools — 00b92ce63593

`reference_probe.py` is an independent Python mirror of the selected rule and
of the two strongest shortcuts that fit every canonical demonstration:
`only_color7` and `keep_off_legend`.  It does not import implementation helpers
from `generator.py`.

From the repository root in a prepared review runtime:

```bash
PYTHONPATH=src:shared/runtime python3 -B \
  generators/00b92ce63593/workspace/reference_probe.py \
  --per-band 500 --out /tmp/00b92ce63593-probe.json
```

The report binds the generator SHA-256 and records canonical rival fit,
deterministic replay, distinct inputs, schedule-profile counts, self-check
errors, and how often each rival disagrees with the independent authority.
The repository battery remains the source of real Racket parity evidence.
