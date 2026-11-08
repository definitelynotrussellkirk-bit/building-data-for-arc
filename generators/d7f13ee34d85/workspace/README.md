# Reusable canonical behavior check

From the repository root, with its public runtime on PYTHONPATH:

```bash
PYTHONPATH=src:shared/runtime python3 generators/d7f13ee34d85/workspace/canonical_behavior_gate.py --lesson-target-feature negative_centering_offset --out coverage.json
```

The supported packet wrapper can run the same script through `python3 review.py run ABSOLUTE_PYTHON ...` from the outer packet. The payload works in `WORK/repo`; use an absolute interpreter path.

Defaults are 20 ordinary seeds at index zero and ten raw consecutive three-demo/one-query windows per band (including default). `--generator-file` compares a retained baseline. `--bands`, `--samples`, `--lessons`, `--seed`, `--sample-index`, `--demos` and `--lesson-stride` make the budget and sampling explicit. `--out` must be new.

Exit 0 means bounded feature support; exit 1 means missing ordinary support or an explicitly required lesson feature; exit 2 means execution/provenance error. The report retains canonical/generated witness inputs, source and rule-text hashes, every seed/index, unique-input counts, and per-lesson support. Source drift during a run is an error.

This is an input-behavior gate. It does not generate output labels, execute Racket or claim production lesson identifiability. The public `arcpuzzles lesson-census` performs that separate source-bound check with actual Racket labels. Small budgets can miss a legitimately rare branch; interpret support frequency and the declared training mixture before changing policy. A new task needs its own justified feature extractor, not this task's frame assumptions.
