# Workspace

The selected implementation is `../generator.py`. Workspace drafts are never automatically selected.

`probe_shortcuts.py` is the retained reusable rival-rule probe. It reads the generator's exported `CANONICAL_SHORTCUTS`, `LESSON_COMPETITORS`, `SEMANTIC_WITNESSES`, and schedule declarations; verifies every declared canonical shortcut against every usable canonical pair; checks every cyclic lesson start; and records an emitted exact four-connectivity counterexample. Run it from the packet root:

```bash
PYTHONPATH=repo:repo/src:repo/shared/runtime python3 \
  repo/generators/eefadafb2b7b/workspace/probe_shortcuts.py \
  --out checks/eefadafb2b7b-shortcut-probe.json
```
