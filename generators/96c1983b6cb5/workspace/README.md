# Workspace

`reference_probe.py` is the task-local independent oracle and repeatable audit
for generator `96c1983b6cb5`. It deliberately does not import transform or
validation helpers from `../generator.py`. With `--racket`, it requires actual
selected-authority execution and fails rather than falling back silently.

Example from the packet root:

```bash
python3 run_with_racket.py python3 generators/96c1983b6cb5/workspace/reference_probe.py \
  --count 140 --out ../checks/reference-probe.json --racket
```

The selected implementation is `../generator.py`; workspace code is reviewer
evidence and is never automatically selected for generation.
