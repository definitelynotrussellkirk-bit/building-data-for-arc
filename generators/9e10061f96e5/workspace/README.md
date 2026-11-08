# H118 review workspace

`probe_curriculum.py` is a source-bound, public-interface probe for future
reviewers. It checks:

- exact `n_panels` overrides in every band;
- all 22 possible relation-matrix outputs for 2–4 panels;
- ordered easy/medium/hard default panel-count means;
- every cyclic five-example lesson start in every band;
- all declared semantic witnesses and rival disagreements; and
- observed 3–8-cell shape-size support.

Run from the repository root:

```bash
PYTHONPATH=shared/runtime python3 \
  generators/9e10061f96e5/workspace/probe_curriculum.py \
  --samples 100 --json-out ../checks/curriculum-probe.json
```

The script also locates the portable task-test runtime automatically, so the
same probe runs inside the isolated snapshot used by `arcpuzzles check ...
--stage task_tests`.
