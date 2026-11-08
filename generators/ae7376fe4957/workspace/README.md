# Workspace

`shortcut_audit.py` is a portable, declaration-driven reviewer probe for this task. It:

1. evaluates every current `CANONICAL_SHORTCUTS` entry on the canonical pairs;
2. finds one emitted counterexample per declared shortcut; and
3. checks every query position in deterministic four-pair lesson windows.

Run it inside a staged task runtime, for example:

```bash
python3 workspace/shortcut_audit.py --seeds 16 --starts 48 --out shortcut-audit.json
```

The selected implementation remains `../generator.py`; workspace tools are not automatically selected as generators.
