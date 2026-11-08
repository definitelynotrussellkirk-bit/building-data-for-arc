# Task-local review tools — c00a9bcded8e

The selected implementation is `../generator.py`. These files are review tools,
not alternate generators and not a label authority.

From the repository root, run the independent distribution/lesson audit with:

```bash
python3 -B generators/c00a9bcded8e/workspace/distribution_probe.py \
  --per-band 100 --out /tmp/c00a9bcded8e-distribution.json
```

`distribution_probe.py` can run from any working directory. It independently
extracts solid rectangles, compares generated rectangle dimensions with the four
canonical pairs, measures unique spatial layouts, scores the generator's actual
`LESSON_COMPETITORS` and `CANONICAL_SHORTCUTS` declarations, checks every
production three-demo sliding window, and rotates every sample in six-item blocks
through the query position while keeping one demonstration from each schedule
slot. It checks Python generation and lesson construction only; the repository
battery remains the source-bound Racket authority check.
