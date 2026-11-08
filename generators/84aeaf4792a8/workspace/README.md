# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here.
The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

## Source-bound distribution probe

`probe_distribution.py` is a reusable **authoring-only** probe. From the
extracted packet's `WORK` directory:

```bash
python3 ../review.py run python3 generators/84aeaf4792a8/workspace/probe_distribution.py \
  --per-band 128 --seed 1729 --out ../checks/distribution/run-1729
```

The output directory must be new. The probe retains every exact input, replay
parameters, independent pixel-oracle result, and public `Catalog.apply` Racket
result. Its report records generator/rule/probe/oracle hashes; per-band counts,
partitions, shape support and input/output uniqueness; actual namespaced rival
declarations; canonical fit checks; and the first exact refutation of each rival.
Invalid inputs, source drift, canonical shortcut misdeclarations, authority
errors, and oracle/Racket disagreements cause a nonzero exit with retained
evidence. `receipt.json` records the payload command, working directory, exit
code, and hashes of the evidence files.

This script reads canonical answers, so keep its output outside solve folders.
It measures a finite sample of individual inputs. Use the public
`arcpuzzles lesson-census` command to test assembled lessons and query holdouts.
