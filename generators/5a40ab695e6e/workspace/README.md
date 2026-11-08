# Workspace — `5a40ab695e6e`

`semantic_probe.py` is a source-bound regression/census tool for the repaired
symmetry-signature generator. It complements the shared Racket-backed lesson
census by checking two task-specific risks:

1. every choice of masked query in each four-pair lesson still leaves three
demonstrations that refute the canonical-fitting `bbox_area_lookup` shortcut;
2. every joint `grid_h × grid_w × n_objects` override combination is
constructive and exactly observable in all three difficulty bands.

It also saves a concrete counterexample grid, the symmetry-rule output, the
rival output, replay coordinates, profile counts, and input hashes.

From the repository root:

```bash
PYTHONPATH=shared/runtime:src:. \
  python3 generators/5a40ab695e6e/workspace/semantic_probe.py \
  --lessons-per-band 100 \
  --out ../checks/semantic-probe.json
```

This probe uses the Python rule mirror. Use the official battery semantic gate
and shared `lesson-census` command for Racket-backed equivalence evidence.
