# Workspace

The selected implementation is `../generator.py`; workspace tools are not selected as generators.

## `probe_shortcuts.py`

Reproduces the strongest canonical-fitting shortcut (`spaced_only`), checks all five canonical pairs, applies the canonical Racket rule to an exact adjacent-span counterexample, and checks 72 consecutive three-demonstration teaching windows (24 per difficulty band). From the extracted packet root:

```bash
python3 run_with_racket.py python3 generators/0d877a4c52fd/workspace/probe_shortcuts.py \
  --out ../checks/shortcut-witness.json
```

The resulting JSON is source-bound and records the input/output hashes, the differing cell, canonical fit count, sampled span support, and authority receipt.
