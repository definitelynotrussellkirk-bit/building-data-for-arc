# Workspace

`reference_probe.py` is a reusable, task-local semantic probe. It independently parses the 3×3 code, renders the intended 9×9 output, evaluates every rival declared by the selected generator, checks exact counterexamples, optionally compares against the real Racket authority, measures band support/determinism, and tests cyclic lesson windows.

From the packet's `repo/` directory:

```bash
python3 generators/0ab4fcb302d2/workspace/reference_probe.py \
  --count 500 \
  --out ../checks/review_analysis/semantic_probe.json
```

The production sampler remains authoritative for duplicate rejection and lesson assembly. Run it separately from the packet root:

```bash
python3 run_with_racket.py python3 -m arcpuzzles lesson-census \
  0ab4fcb302d2 --per-band 100 --rotate-query --timeout 1800 \
  --out ../checks/lesson-census.json
```

The selected implementation is `../generator.py`. Workspace files are probes and documentation; they are not automatically selected as generator source.
