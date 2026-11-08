# Workspace

The selected implementation is `../generator.py`. Workspace files are diagnostics and are never automatically selected.

## `profile_probe.py`

Fast task-local coverage probe. It samples all difficulty bands, reports observed scene profiles, canonical profile rate, semantic witness hits, and per-shortcut counterexamples. It also confirms that each declared canonical shortcut still fits every canonical pair using the Python audit mirror.

From the packet root:

```bash
python3 repo/generators/2fd7d58a066c/workspace/profile_probe.py \
  --draws-per-band 20 \
  --out repo/generators/2fd7d58a066c/workspace/profile_probe_after.json
```

The saved `profile_probe_after.json` is the 2026-10-02 run. This tool does **not** replace the Racket-backed battery; it is intended for quick distribution regression and exact counterexample inspection.
