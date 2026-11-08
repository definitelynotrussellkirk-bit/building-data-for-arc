# Workspace

The selected implementation is `../generator.py`. Workspace programs are retained
authoring and audit aids; they are not automatically selected at runtime.

## `probe_declared_rivals.py`

Dynamically loads the selected generator, discovers its actual
`CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, and `SEMANTIC_RIVALS`, checks each
shortcut against every usable canonical training pair, and scans generated draws
for the first prediction disagreement.

Run from `repo/`:

```bash
PYTHONPATH=shared/runtime:. python3 \
  generators/6c40e60caa4a/workspace/probe_declared_rivals.py \
  --seeds 8 --indices 8 \
  --out ../checks/shortcut-counterexample/declared-rivals-probe.json
```

The program's intended-output calculation is a Python mirror for fast probing.
Confirm retained claims with the supported Racket `arcpuzzles apply` command; the
Racket-backed witness is under `../../../../checks/shortcut-counterexample/` in the
review packet and copied to `../counterexamples/` for regression coverage.
