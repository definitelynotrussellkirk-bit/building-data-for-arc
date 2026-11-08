# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Source-bound lesson probe

`lesson_probe.py` is a reusable curriculum audit for this task. It imports the selected generator, verifies the declared canonical shortcuts against every usable canonical pair, assembles disjoint five-pair windows, checks all cyclic schedule starts, and reports lesson identifiability, uniqueness, profile counts, semantic witnesses, rival disagreements, exact observed axis values, source hashes, and domain limits.

Run from the packet root:

```bash
PYTHONPATH=repo/shared/runtime:repo/src \
python3 repo/generators/0f423424b1dc/workspace/lesson_probe.py \
  --per-band 100 \
  --expected-generator-sha bc41dfd17675af9b71ba310882da7d02dd02894c80c2b7948eaec2be0160c85d \
  --out checks/lesson_probe_100_per_band.json
```

The retained final report is `checks/lesson_probe_100_per_band.json`. Its output oracle is the task-local Python mirror for speed; use the independent battery reports under `checks/after/` to establish Racket parity.
