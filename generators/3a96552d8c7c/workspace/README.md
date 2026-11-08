# Workspace

The selected implementation is `../generator.py`. This workspace contains source-only review tools that future agents can run before the full repository battery.

## Qualification probe

From `repo/`:

```bash
PYTHONPATH=shared/runtime python3 generators/3a96552d8c7c/workspace/qualify.py \
  --per-band 100 --starts 12 --seed 20261004 \
  --out ../checks/source-qualification.json
```

The probe checks:

- all canonical inputs against the reviewed validator and Python rule mirror;
- 100 draws per difficulty band, uniqueness, strict acceptance, profile coverage, and witness frequency;
- exact observable overrides across reviewed boundary cases;
- every query rotation for all three-slot schedule starts against the generator's actual declared rivals.

It is deliberately source-only. Use the repository battery for canonical Racket execution, source synchronization, grammar, and authority parity:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 3a96552d8c7c \
  --battery --timeout 4000 --phase after --out ../checks/after
```

`reference_probe.py` centralizes canonical/source lookup for the qualification tool. Do not use either helper during a visible-only solve.
