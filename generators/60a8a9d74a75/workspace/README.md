# Workspace

The selected implementation is `../generator.py`. Workspace files are diagnostic
and are never selected automatically.

## Independent region and rival probe

`reference_probe.py` independently recomputes 4-connected zero regions and the
intended fill rule; it does not call `generator.rule_mirror`. It loads the current
generator only to obtain generated inputs and iterate the generator's declared
`LESSON_COMPETITORS`.

Inspect one retained shortcut witness from the repository root:

```bash
python3 generators/60a8a9d74a75/workspace/reference_probe.py \
  --seed 901 --sample-index 1 --difficulty hard \
  --profile composite_open_left --out /tmp/region-probe.json
```

Scan consecutive ordinary draws:

```bash
python3 generators/60a8a9d74a75/workspace/reference_probe.py \
  --seed 10000 --sample-index 0 --difficulty hard \
  --scan 400 --out /tmp/region-scan.json
```

The single-sample report includes every zero region, neighboring colors, edge
contact, independent reference output, and each declared rival output. The scan
reports crashes, unique inputs, profile counts, changed-cell range, maximum zero
region size, and disagreement counts. Focused tests verify standalone runtime
bootstrapping and compare its output with the production mirror.
