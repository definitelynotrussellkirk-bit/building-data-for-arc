# Workspace

`probe_shortcuts.py` is the reusable source-bound shortcut probe for this task. It dynamically scores every declared `CANONICAL_SHORTCUTS` predictor against retained canonical pairs, finds a lawful generated disagreement for the strongest surviving rival, and emits `input.json` plus a Python report. Use the public `arcpuzzles apply` command on that input for Racket authority.

Example from the packet root:

```bash
python3 review.py run python3 generators/4c93dc1552b3/workspace/probe_shortcuts.py \
  --out-dir ../checks/generator-shortcut-new
python3 review.py run python3 -m arcpuzzles apply 4c93dc1552b3 \
  --input ../checks/generator-shortcut-new/input.json \
  --out ../checks/generator-shortcut-new/racket.json
```

Keep alternate drafts, reproducers, and unfinished experiments here. The selected implementation is `../generator.py`; workspace drafts are never automatically selected.
