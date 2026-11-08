# Workspace

The selected implementation is `../generator.py`; workspace files are not selected automatically.

`reference_probe.py` is a source-bound future-agent tool for this task. It:

- independently interprets the documented directional-ray rule;
- checks every canonical input/output pair and the declared canonical-fitting rival;
- samples default/easy/medium/hard modes for validity, determinism, witness support, shapes, and unique inputs;
- optionally executes the real Racket authority with `--racket` and reports parity failures explicitly rather than falling back silently.

Example from a prepared repository/runtime:

```bash
python3 generators/be6269bef667/workspace/reference_probe.py \
  --count 250 --racket --out ../checks/be6269bef667-reference-probe.json
```
