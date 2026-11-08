# Task-local reviewer tools

`probe_controls.py` checks the exact-control contract without canonical answers:

```bash
python3 generators/8de1c257a9c7/workspace/probe_controls.py \
  generators/8de1c257a9c7/generator.py \
  --out ../checks/control-probe.json
```

It exhausts every schedule slot across two seeds and reports whether explicit
`None` is a no-op, same-value overrides preserve the exact scheduled instance,
dimension overrides leave unpinned axes unchanged, and coercive integer values
are rejected. The JSON includes the generator SHA-256 for replay.
