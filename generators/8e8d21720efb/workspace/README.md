# Reviewer workspace

`locality_shortcut_probe.py` is a cheap, source-bound authoring probe for this
task. It independently computes the selected same-colour-cardinal law and the
canonical-fitting global-frequency shortcut, then reports ordinary-example
agreement and every held-out-query rotation of consecutive four-pair windows.

From `WORK/repo/`:

```sh
python3 generators/8e8d21720efb/workspace/locality_shortcut_probe.py \
  --generator generators/8e8d21720efb/generator.py \
  --per-band 100 \
  --out ../checks/locality-shortcut-final.json
```

The full Racket-labelled `lesson-census` remains the authority check; this probe
is intentionally faster and useful before that larger run.
