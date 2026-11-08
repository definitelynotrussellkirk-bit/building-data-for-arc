# 22304ccc509c workspace

`probe_shortcuts.py` is a reusable, deterministic task-local audit for the two
published rivals.  It verifies that the declared canonical shortcut really fits
all canonical labels, measures every witness/rival over each difficulty band,
and exhaustively rotates the query through consecutive four-pair lesson windows.
It uses the generator's independent Python mirror; pair it with the official
Racket battery and lesson census for authority-backed labels.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/22304ccc509c/workspace/probe_shortcuts.py \
  --per-band 100 --starts 25 --out ../checks/shortcut-probe.json
```

The report is source-hashed and exits nonzero on validator failures, missing
witnesses, surviving declared rivals, or ambiguous cyclic rotations.
