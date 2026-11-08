# Workspace

The selected implementation is `../generator.py`.

`reference_probe.py` is an independent, portable reviewer probe. It reads
canonical pairs through `reviewer_support`, transcribes the selected rule without
importing production geometry, audits observed axes, and counts witness/rival
coverage across all bands.

From the packet root:

```bash
python3 run_with_racket.py python3 generators/4f6f232c17bc/workspace/reference_probe.py \
  --count 40 --json-out ../checks/after/reference-probe.json
```

The final report used 40 draws per band (120 total). Workspace tools are review
evidence only and are never selected as the production generator.
