# Reviewer workspace

- `generator-v1.4.1-before.py` is the pinned pre-repair source used for the baseline diagnosis.
- `probe_curriculum.py` is a reusable task-local census. It checks exact observable overrides, every consecutive start in a small period, every five-pair query rotation, and the generator's declared lesson competitors/canonical shortcuts.

Run from `repo/`:

```bash
PYTHONPATH=shared/runtime:shared/tools python3 \
  generators/0e4adc584fa1/workspace/probe_curriculum.py \
  --period 20 --seeds 8 \
  --out ../checks/curriculum-probe.json
```

The probe is deliberately finite. A pass establishes coverage only against the declared rival class over the reported seed/start range; it is not a universal induction proof.
