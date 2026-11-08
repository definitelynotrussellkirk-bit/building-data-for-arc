# Portable authoring probe

`probe.py` emits 64 cases: all three canonical labeled pairs, all 32 joint
minimum/maximum axis corners, and 29 default draws. It independently computes
row-segment reflection expectations, checks every currently declared canonical
shortcut, and enumerates actual lesson-competitor refutations. It does **not**
create production labels or replace the Racket authority. Do not use it during
a blind/visible-only solve.

From the extracted packet root (choose fresh output directories):

```sh
python3 run_with_racket.py python3 generators/ba29d14676d1/workspace/probe.py --out ../checks/reference-probe
python3 run_with_racket.py python3 -m arcpuzzles apply ba29d14676d1 --input ../checks/reference-probe/inputs.json --out ../checks/reference-probe/racket.json
python3 run_with_racket.py python3 -m arcpuzzles check ba29d14676d1 --stage task_tests --timeout 600 --phase after --out ../checks/task-tests
```

Compare each `racket.json.results[i].output` to `probe.json.cases[i].expected`;
require valid_output and no error. The return includes checks/verify_authorities.py
which performed this exact comparison and retained an emitted five-shortcut
counterexample. The tool uses public reviewer_support root/canonical helpers and
works in normal and staged layouts. It fails rather than overwrite an existing
probe directory. Tests dynamically read current rival declarations.

For stronger lesson evidence use the shared lesson-census command. The task tests
also enumerate every declared joint control tuple in three bands and all cyclic
starts of a small six-pair-window sample. Treat overlapping windows as correlated
coverage checks, not independent statistical trials. Production-shape lessons
need five demos; arbitrary resampling or witness-removing overrides are not
covered by the default schedule guarantee.
