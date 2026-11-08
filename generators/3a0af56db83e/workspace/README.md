# Workspace

`overlap_arity_probe.py` is a reusable reviewer probe for this generator. It reads canonical answers, iterates the generator's declared `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, models production lessons with one shared seed and consecutive sample indices, checks every cyclic schedule start requested, measures projected occupancy arities, and emits an exact generated color-priority counterexample.

Run from the repository root:

```bash
PYTHONPATH=src:shared/runtime python3 generators/3a0af56db83e/workspace/overlap_arity_probe.py \
  --samples 16 --starts 16 \
  --out ../checks/overlap-arity-probe-final.json \
  --counterexample-out ../checks/shortcut/3a0af56db83e-final/input.json
```

The final retained run checked 48 same-seed cyclic lessons (16 starts × 3 bands) with no declared rival surviving and changing the query, plus 144 distribution draws (16 samples × 3 widths × 3 profiles), all unique, all covering overlap arities 0–4, and all preserving exact profile observability.

This is evidence code, not production code. It uses canonical outputs and must not be run during a visible-only solve.
