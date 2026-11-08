# Reusable semantic probe

`semantic_probe.py` discovers the current task/root using the shared portable
helpers. It reads every usable canonical pair and calls the actual functions
in `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_RIVALS`.
It saves 17 explicit inputs, independent geometry predictions, all declared
rival predictions, validator findings, and source/rule hashes. Its `compare`
step requires the public Racket receipt; Python geometry alone is never
reported as reference execution.

With the packet's Python dependencies and Racket runtime set up, run from
`repo`:

```bash
PYTHONPATH=shared/runtime python3 -B generators/139d29b1283d/workspace/semantic_probe.py prepare --out ../checks/new-probe
```

From the packet root:

```bash
python3 run_with_racket.py python3 -m arcpuzzles apply 139d29b1283d --input ../checks/new-probe/input.json --out ../checks/new-probe/racket.json
```

Then from `repo`:

```bash
PYTHONPATH=shared/runtime python3 -B generators/139d29b1283d/workspace/semantic_probe.py compare --out ../checks/new-probe --racket ../checks/new-probe/racket.json
```

Use a new output directory for each source version. Read `verified.json` for
per-rival results and validator/domain qualifications. This is a source-aware
counterexample tool, not a replacement for materialized lesson censuses.
Do not use it during a visible-only solve: canonical helpers expose labels.

The accepted implementation is `../generator.py`; workspace tools are never
automatically selected as generators. Original baseline and intermediate
investigation evidence are retained in the review return's `checks/` tree.
