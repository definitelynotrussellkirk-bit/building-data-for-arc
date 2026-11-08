# 01bdf9b8d2db review workspace

`lesson_probe.py` is the source-bound audit for the repaired generator. It:

- reproduces the semantic gate's per-band lesson sampler (`k * 11` starts and pinned SHA-256 seeds);
- evaluates every declared `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_WITNESSES` entry rather than copying names;
- records 100+ complete lessons per band, unique input hashes, competitor disagreements, schedule coverage, domain limits, and exact source hashes;
- checks an independent Python connectivity oracle against every canonical pair; and
- with `--racket`, executes all canonical and generated grids with the selected canonical Racket source in a staged runtime, with no fallback.

From the packet root:

```bash
python3 run_with_racket.py python3 generators/01bdf9b8d2db/workspace/lesson_probe.py \
  --lessons-per-band 100 --racket \
  --out ../checks/lesson_probe_final.json \
  --counterexample-out ../checks/shortcut_counterexample.json
```

The script path in that example is relative to `repo`; `run_with_racket.py` changes into `repo` before execution.
