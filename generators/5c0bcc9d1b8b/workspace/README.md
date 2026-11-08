# Task-local review tools

`probe_contract.py` is a deterministic, source-bound maintainer probe. It checks the Python rule mirror against every labeled canonical pair, verifies that the declared `canonical_size_to_count` shortcut fits those pairs, exhausts every exact `scene_profile`, confirms override observation and the declared output codomain, and retains one exact distinguishing input.

From `WORK/`:

```sh
python3 run_with_racket.py python3 generators/5c0bcc9d1b8b/workspace/probe_contract.py \
  --out ../checks/contract-probe.json
python3 run_with_racket.py python3 -m pytest -q \
  generators/5c0bcc9d1b8b/workspace/test_probe_contract.py
```

The probe's intended outputs use the task-local Python mirror for cheap exhaustion. Confirm a retained witness independently with the supported Racket command, as done in `checks/counterexamples/5c0bcc9d1b8b/racket.json`; the mirror is not a replacement authority.
