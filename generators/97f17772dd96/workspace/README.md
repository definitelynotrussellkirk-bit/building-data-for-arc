# Workspace

The selected implementation is `../generator.py`; files here are authoring and
reproduction utilities and are never selected automatically.

`build_counterexample.py` regenerates the retained `concentric_only` shortcut
witness, labels it with the selected Racket authority, checks the Python mirror,
and records the exact source hash. From `WORK/` run:

```bash
python3 run_with_racket.py python3 \
  generators/97f17772dd96/workspace/build_counterexample.py \
  --out generators/97f17772dd96/counterexamples/concentric-only-offset-inner/counterexample.json
```
