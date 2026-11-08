# Workspace

The selected implementation is `../generator.py`. Workspace scripts are diagnostics and are never automatically selected.

## `probe_consensus_contract.py`

Cheap source-bound Python probe for future reviewers. It checks:

- generator `self_check` and an independent cell-law mirror,
- every declared `LESSON_COMPETITORS` rival,
- every declared `CANONICAL_SHORTCUTS` claim against usable canonical pairs,
- required branch minima, sampled profiles, and exact-axis support by band.

From `repo/`:

```bash
PYTHONPATH=src:shared/runtime python3 generators/083ba0fc4534/workspace/probe_consensus_contract.py \
  --per-band 100 --seed-base 10000 --out ../checks/consensus-probe.json
```

This is an early diagnostic, not an authority check. Use the Racket battery and `lesson-census` for acceptance.
