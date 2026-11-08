# Workspace

The selected implementation is `../generator.py`. Workspace files are review probes and are never automatically selected as production code.

## `profile_probe.py`

A deterministic, reusable curriculum census. It generates 20 draws in each difficulty band, records profile balance and strict-canonical support, runs `self_check`, measures every semantic witness, checks refutation frequency for each canonical-fitting shortcut, and verifies one scheduled four-demo lesson with `lesson_identifiable`.

Reproduce from the packet root:

```bash
PYTHONPATH=repo/shared/runtime python3 \
  repo/generators/4cfd24806fb2/workspace/profile_probe.py \
  --seed 20261002 --draws-per-band 20 \
  --out repo/generators/4cfd24806fb2/workspace/profile_probe_after.json
```

The retained result has 60 total draws, 15 per profile, a 25% strict rate in every band, no self-check failures, live coverage for all six witnesses, and nonzero refutations for all six canonical-fitting shortcuts.
