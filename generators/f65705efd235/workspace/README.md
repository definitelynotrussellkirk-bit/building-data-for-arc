# Workspace

Keep alternate drafts, reproducers, and unfinished experiments here. The selected implementation is `../generator.py`.

## Retained probe

`probe_generator.py` is a deterministic, task-local regression census. It checks canonical Python-mirror parity, exact boundary overrides, object-count delivery, thin-rectangle and overlap coverage, all semantic witness/rival pairs, and every three-example schedule window.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/f65705efd235/workspace/probe_generator.py \
  --draws-per-band 2000 --json-out ../checks/f65705efd235-probe.json
```
