# Task 83efd4fcb4f4 review workspace

`plus_probe.py` is an independent Python oracle and curriculum probe. It does
not import `generator.py`; task-local tests use it to catch production mistakes.

Run a reproducible 20-sample-per-band report from the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/83efd4fcb4f4/workspace/plus_probe.py \
  --generator generators/83efd4fcb4f4/generator.py \
  --samples 20 --out ../checks/plus-probe.json
```

The report records target counts, distractor components, four semantic witness
frequencies, and disagreement against four finite wrong-rule competitors.
