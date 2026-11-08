# d8a6f767016a review workspace

`shortcut_probe.py` verifies the strongest visible-demo shortcut found in this
review: mapping each 8-component's **cell count** through four size bins instead
of counting enclosed zero-regions. It confirms the rival fits all four canonical
training demonstrations, checks an exact two-object counterexample, and measures
whether ordinary generated draws expose the disagreement.

From a staged reviewer runtime:

```bash
python3 puzzle_generators/per_puzzle/d8a6f767016a/workspace/shortcut_probe.py \
  --racket-result shortcut-counterexample-racket.json \
  --out shortcut-probe-report.json
```

Generate `shortcut-counterexample-racket.json` with `arcpuzzles apply` first;
the workspace script treats that executed canonical result as authority.
