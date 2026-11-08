# Task-local review tools

`reference_probe.py` is the reusable independent probe for this task. It does not use the generator's label helpers: it reconstructs the rotation from pixels, checks canonical parity, executes the `code_one_is_clockwise` and `strip_unrelated_objects` rivals, samples generated inputs, and emits an exact code-1 disagreement witness.

Example from the repository root:

```bash
python3 generators/c3052979ff96/workspace/reference_probe.py \
  --generated 100 \
  --json-out ../checks/reference-probe.json
```

The selected implementation remains `../generator.py`; workspace tools are supplemental evidence only.
