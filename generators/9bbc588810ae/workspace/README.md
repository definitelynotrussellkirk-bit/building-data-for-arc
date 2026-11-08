# Workspace probes for `9bbc588810ae`

`probe_contract.py` is a reusable source-bound check for the repaired sampler. It verifies all canonical pairs with the independent Python mirror, samples every difficulty band, records exact axis coverage and diversity, tests all four query rotations of overlapping four-pair windows, and saves the first generated counterexample to the canonical-fitting `bbox_count_lowest_color` rival.

From the extracted packet root:

```bash
python3 run_with_racket.py python3 generators/9bbc588810ae/workspace/probe_contract.py \
  --per-band 40 --racket --out ../checks/contract-probe-final.json
```

The optional `--racket` mode uses public `Catalog.apply(reference="canonical")` for the three canonical inputs and the retained generated counterexample, and binds the receipt to both generator and rule hashes. Without `--racket`, the structural, schedule, and Python-mirror checks remain useful in a plain runtime.

The probe is evidence against the declared rival over the checked finite population; it is not a proof against every imaginable shortcut.
