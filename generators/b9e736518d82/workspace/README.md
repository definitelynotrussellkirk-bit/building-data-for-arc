# Workspace

`reference_probe.py` is the retained independent audit tool for this task. It:

- reads all canonical pairs and the canonical Racket program;
- reconstructs the authority-selected adjacent-orange component independently
  of `generator.py`;
- orders the latent path and computes exact side/outer-corner walls;
- mirrors the authority output in Python for fast tests;
- implements the three named rivals used by the semantic contract;
- can batch a source-bound sample against the real Racket runtime; and
- emits deterministic per-band distribution counts.

Typical source-tree audit invocation from `repo/`:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/b9e736518d82/workspace/reference_probe.py \
  --generator generators/b9e736518d82/generator.py \
  --count 250 --racket \
  --out ../checks/b9e736518d82_independent_audit.json
```

The selected implementation is `../generator.py`; alternate drafts are not
automatically selected.
