# Recurrence review tools

Run from the extracted packet root after `python3 review.py setup`, with a
Python 3.12+ environment containing pytest, NumPy, and Pillow. Replace the
interpreter paths below if your environment uses another location. The wrapper
runs its payload in `WORK/repo`; output paths beginning `../checks/` therefore
refer to `WORK/checks/`. Choose a fresh output filename on every run.

```bash
WORK/.venv/bin/python review.py run ../.venv/bin/python \
  generators/8e6c44aee812/workspace/probe_recurrence.py \
  --seed 0 --out ../checks/recurrence-replay.json

WORK/.venv/bin/python review.py run ../.venv/bin/python -m pytest -q \
  generators/8e6c44aee812/tests

WORK/.venv/bin/python review.py run ../.venv/bin/python -m arcpuzzles \
  lesson-census 8e6c44aee812 --enumerate-schedule-period --schedule-seed 0 \
  --rotation-policy require --out ../checks/schedule-replay.json
```

`probe_recurrence.py` makes one public reference call for 59 inputs: four
canonical pairs, four exact retained counterexample grids, and 17 generated
inputs per band. It records full labels once, source and executed rule hashes,
the retained 83/100-cell disagreement, and all 12 production starts with each
query holdout. It iterates the selected generator's actual rival declarations
and separately implements the original first-run rival. It refuses to overwrite
evidence and fails on reference errors, source drift, ambiguity, or hook warnings.

Use `--seed` to inspect another signed integer seed and `--demos` to inspect a
shorter teaching hypothesis. A passing report describes only that finite
population. Python expectation helpers in tests are mirrors, while the probe
and public census execute the selected Racket rule for their labels.

The exact intermediate role-conditioned findings are retained under
`../counterexamples/role_conditioned_first_run.json` relative to this directory.
Their regression tests load the saved grids rather than regenerating old indices.
