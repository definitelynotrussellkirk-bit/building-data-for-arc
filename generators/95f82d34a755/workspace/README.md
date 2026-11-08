# Workspace

`probe_canonical_shortcuts.py` is the reusable authoring probe for this task.
It loads the selected generator, checks every declared `CANONICAL_SHORTCUTS`
rule against all canonical pairs, labels the minimum sliding-window draw set
with the canonical Racket rule, audits every five-demo window and every
leave-one-out query rotation, and retains one exact disagreement witness.

From the packet root:

```sh
python3 review.py run python3 \
  generators/95f82d34a755/workspace/probe_canonical_shortcuts.py \
  --out ../checks/canonical-shortcut-probe --seed 20261012 --starts 10
```

Pure helper regressions live in `test_probe_canonical_shortcuts.py`. The selected
implementation remains `../generator.py`; workspace drafts are never selected.
