# Reviewer workspace

`probe_curriculum.py` is a source-bound, task-local probe for the repaired
`a287e878de99` generator. It uses an independent degree-one oracle and checks:

- every declared canonical shortcut against all canonical pairs;
- 16 cyclic lesson starts per difficulty and all five possible query rotations;
- a boundary Cartesian matrix for all advertised overrides.

Run from `repo/`:

```bash
PYTHONPATH=shared/runtime python3 generators/a287e878de99/workspace/probe_curriculum.py \
  --starts 16 --out ../checks/curriculum-probe.json
```

Add `--full-overrides` to enumerate all 5,760 advertised override combinations
across `None`, easy, medium, and hard. The public battery's override stage is the
retained exhaustive authority; this probe is intended for fast iteration and
cyclic curriculum checks.
