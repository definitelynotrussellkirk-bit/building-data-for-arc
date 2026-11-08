# Workspace

## `role_signature_gate.py`

This task-local audit compares canonical and generated histograms of per-color cell multiplicities. It catches curricula that omit the canonical singleton role while still matching coarse canvas and palette marginals.

Run from the repository root:

```bash
python3 generators/39574cf4b561/workspace/role_signature_gate.py \
  --draws-per-band 20 \
  --json-out ../checks/role_signature_gate.json
```

## `lesson_shortcut_audit.py`

This source-bound audit loads the final generator, iterates its actual `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`, and checks every sliding three-demo lesson start over the complete deterministic schedule period. It verifies that each declared canonical shortcut really fits every canonical pair, checks generated inputs with `self_check`, requires both color-9 roles in every lesson, applies `lesson_identifiable`, counts unique inputs, and saves the first exact shortcut disagreement.

The default period is 180, the least common multiple of the scene, missing-corner, singleton-relation, palette, and three-sample color-role schedules.

```bash
python3 generators/39574cf4b561/workspace/lesson_shortcut_audit.py \
  --period 180 \
  --seed 610000 \
  --json-out ../checks/lesson_shortcut_audit_final.json
```

The selected implementation remains `../generator.py`; neither workspace tool is part of generation-time behavior.
