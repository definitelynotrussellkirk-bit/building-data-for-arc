# Reviewer workspace for fdb8815ba528

- `reference_probe.py`: independent canonical loader, same-colour 4-connected component extractor, bbox-outline oracle, axis observer, and strongest alternative rules.
- `exhaustive_contract_probe.py`: enumerates every legal joint exact-axis setting across difficulty bands and seeds, then checks independent observation, self-check, oracle parity, and nontriviality.

From the repository root:

```bash
PYTHONPATH=shared/runtime:generators/fdb8815ba528/workspace \
  python generators/fdb8815ba528/workspace/exhaustive_contract_probe.py \
  --seeds 6 --out ../checks/exhaustive-contract.json
```
