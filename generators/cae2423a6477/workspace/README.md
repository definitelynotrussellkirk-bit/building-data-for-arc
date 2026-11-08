# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here. The
selected implementation is `../generator.py`; workspace drafts are never
automatically selected.

## Rival probe

`rival_probe.py` is a reusable adversarial check for this task. It independently
implements five low-complexity object selectors, keeps only selectors that fit
all canonical pairs, and measures whether any of them survives a complete
three-demonstration generated lesson.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/cae2423a6477/workspace/rival_probe.py \
  --generator generators/cae2423a6477/generator.py \
  --seeds-per-band 100
```

The command prints JSON and exits nonzero if a canonical-fitting rival survives
any sampled lesson. Use `--output PATH` to retain the report and
`--allow-survivors` when intentionally measuring a historical baseline.
