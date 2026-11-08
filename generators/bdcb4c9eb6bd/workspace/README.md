# Workspace

The selected implementation is `../generator.py`. Workspace files are review probes, not alternate selected generators.

## Independent reference probe

`reference_probe.py` independently parses one-gap rectangles, checks all canonical pairs, measures 100 draws per band, tests the `four_by_four_only` rival, and can compare retained grids with real Racket execution when run through the packet wrapper:

```bash
cd packet_root
python3 run_with_racket.py python3 generators/bdcb4c9eb6bd/workspace/reference_probe.py \
  --racket --out ../checks/bdcb4c9eb6bd_reference_probe_racket.json
```

The final retained report is `checks/bdcb4c9eb6bd_reference_probe_racket.json`.

## Authority checker

`check_authority_sync.py` verifies that the selected base solution's `target_code` exactly matches the canonical `program_solution` and reports exact/normalized hashes:

```bash
cd repo
PYTHONPATH=src:shared/runtime python3 generators/bdcb4c9eb6bd/workspace/check_authority_sync.py
```

These probes do not generate training labels. `reference_probe.py` keeps its Python oracle distinct from the real-Racket parity section.
