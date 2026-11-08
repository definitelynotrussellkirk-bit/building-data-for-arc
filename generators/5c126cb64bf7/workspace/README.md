# Rotation-equivalence authoring workspace

The selected implementation is `../generator.py`. Workspace tools never replace
it or supply authoritative task labels. The Python runtime needs the packet's
documented NumPy, Pillow and pytest dependencies; use a separately initialized
packet environment and its supported wrapper.

## Re-score retained public Racket evidence

From the extracted packet's `WORK/` directory:

```sh
python3 run_with_racket.py python3 -B generators/5c126cb64bf7/workspace/summarize_rivals.py \
  --generator generators/5c126cb64bf7/generator.py \
  --census ../checks/lesson-census-v310.json.gz \
  --output ../checks/new-rival-certificate.json
```

The tool accepts JSON or gzip-compressed JSON. It checks the supplied generator
bytes against the census, validates instance and accepted-input hashes, and
requires the local public canonical ledger to match the retained runtime
manifest. It dynamically reads `CANONICAL_SHORTCUTS` and `LESSON_COMPETITORS`,
checks canonical-fit claims, and scores production queries and every single-pair
holdout. One generated refutation per rival includes the exact input, accepted
sample index, seed, band, retained Racket output and rival output. The output
separates distinct rival names from overlapping declaration namespaces.

This is an authoring tool and reads public canonical answers; never use it in a
visible-only solve. It reuses already saved Racket labels and does not invoke
Racket or prove that arbitrary hypotheses are excluded. Its source-mismatch
negative and successful 300-lesson re-score are in the return's
`checks/rival-certificate/`. A mismatched version fails before generator import.
Use the matching historical generator and evidence when inspecting old failures.

## Capture exact subprocess receipts

```sh
python3 repo/generators/5c126cb64bf7/workspace/record_command.py \
  --cwd . --out checks/new-command \
  --source repo/generators/5c126cb64bf7/generator.py -- \
  python3 run_with_racket.py python3 -m arcpuzzles check 5c126cb64bf7 \
  --stage task_tests --phase after --out ../checks/new-task-tests
```

The recorder runs an argument array without a shell, streams combined output,
records actual cwd/times/exit status and source hashes before/after, and refuses
to overwrite a receipt prefix. The child command owns its timeout and isolation
policy. Receipt-relative paths follow the recorder's invocation directory;
payload paths used by `run_with_racket.py` resolve from `repo/`.

## Tests and retained examples

Run the selected task tests explicitly through `arcpuzzles check --stage
task_tests`; a general repository run is not a substitute. They use portable
`reviewer_support` helpers and an independent cropped-array rotation oracle.
`../counterexamples/` contains an actual final generated reflection negative,
two separately marked authored witnesses, and the intermediate half-turn lesson
failure. All label-authority claims link to retained public Racket receipts.
`implementation-plan.md` records the completed repair and handoff work.
