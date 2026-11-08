# Workspace

`reference_probe.py` independently parses generated/canonical instances and implements the rule mirror used by task tests. `audit_contract_probe.py` reproducibly checks the two drawn audit targets with exact source hashes, seeds, overrides, emitted grids, and validator diagnostics.

The selected implementation is `../generator.py`; workspace files are support tools and are never automatically selected.
