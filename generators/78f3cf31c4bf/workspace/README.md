# Task-local review workspace

The selected implementation is `../generator.py`. The regression suite and
probe intentionally load that exact sibling file, so copied runtimes do not
silently test another catalog version.

From the extracted packet root:

```sh
python3 run_with_racket.py python3 -m pytest -q generators/78f3cf31c4bf/tests
python3 run_with_racket.py python3 generators/78f3cf31c4bf/workspace/review_probe.py \
  --seeds 24 --indices 12 --out ../checks/focused-semantic.json
```

`review_probe.py` binds its report to the generator SHA-256, checks every
currently declared canonical shortcut against all public pairs, counts every
currently declared witness, and rotates consecutive three-example lessons
through every schedule residue. It is a focused authoring probe, not a substitute
for the inherited full battery, real-Racket rule smoke, or the 100-per-band
production lesson census.
