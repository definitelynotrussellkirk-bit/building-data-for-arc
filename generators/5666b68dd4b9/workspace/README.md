# Workspace

`review_probe.py` is the retained semantic review tool for task `5666b68dd4b9`. It:

- materializes one four-demonstration lesson plus query,
- checks every declared lesson competitor and semantic witness,
- finds an emitted selector-color/transform-code shortcut counterexample,
- records self-check and observed-axis results, and
- optionally executes the protected canonical Racket rule.

From the repository root:

```bash
PYTHONPATH=shared/runtime python3 generators/5666b68dd4b9/workspace/review_probe.py   --seed 0 --start 0 --difficulty hard
```

With protected Racket verification:

```bash
RACKET_PATH=/path/to/racket PYTHONPATH=shared/runtime python3 generators/5666b68dd4b9/workspace/review_probe.py   --seed 0 --start 0 --difficulty hard --racket --out /tmp/probe.json
```

The tool supports both the source repository layout (`shared/tools`) and exported review runtime layout (`scripts`). The selected implementation remains `../generator.py`; workspace tools are never automatically selected as generators.
