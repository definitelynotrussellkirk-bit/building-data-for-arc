# Workspace

The selected implementation is `../generator.py`. Workspace files are review tools and are never selected as the production generator.

## Independent curriculum probe

`reference_probe.py` independently reimplements component extraction, positional ordering, unobstructed visibility, exact control observation, and the blocker-blind rival. It does not call generator-private geometry helpers. Optional `--racket` mode executes the canonical Racket rule and fails rather than silently falling back.

From the packet root:

```bash
python3 run_with_racket.py python3 \
  generators/f41ae450c30b/workspace/reference_probe.py \
  --per-band 250 \
  --out ../checks/reference-probe/report.json \
  --racket --racket-samples 96
```

The retained review run audited 750 generated inputs and 100 direct Racket cases; see `checks/reference-probe/report.json`.
