# Workspace tools

`shortcut_probe.py` is a deterministic semantic census for this task. It checks
that generated examples pass both validators, match canonical input profiles,
exercise every scheduled profile, refute every named shortcut, and leave no
shortcut alive across any sliding five-demo lesson.

From `repo/`:

```bash
PYTHONPATH=shared/runtime python3 generators/7aed1f233b46/workspace/shortcut_probe.py \
  --seed 901002 --samples 60 --difficulty hard --strict
```

The JSON output is suitable for retention as a review receipt. The selected
implementation remains `../generator.py`; workspace tools are never selected as
the production generator.
