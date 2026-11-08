# Workspace

`probe_curriculum.py` is a replayable Python-only authoring probe for the selected generator. It checks:

- ownership and mirror equality for all canonical pairs;
- all 72 exact joint axis products;
- declared canonical rival fit;
- every held-out query position in consecutive four-pair windows across all difficulty bands.

Example:

```bash
python3 repo/generators/a5ad56f1e9d4/workspace/probe_curriculum.py \
  --samples-per-band 18 \
  --output checks/a5ad56f1e9d4-workspace-probe.json
```

The probe uses the Python mirror and is not independent authority evidence. Pair it with the Racket-backed battery and lesson census. The selected implementation remains `../generator.py`; unfinished experiments should stay in this directory and are never selected automatically.
