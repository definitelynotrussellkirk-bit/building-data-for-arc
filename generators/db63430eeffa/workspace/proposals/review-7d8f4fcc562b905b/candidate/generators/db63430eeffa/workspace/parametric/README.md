# Proposed path-selection parameter

This **task-local, unselected prototype** keeps the canonical endpoint finding,
row/column step calculation, major-axis choice, endpoint colors, and path color.
It varies one hidden rule parameter fixed for the entire episode:

- `path_mode=both` — original/default behavior and the exact canonical Racket
  source: paint the union of the diagonal-first and straight-first paths.
- `path_mode=diagonal_first` — paint only the diagonal-then-straight path.
- `path_mode=straight_first` — paint only the straight-then-diagonal path.

Every retained setting uses the same input seed and ordering, three
Demonstrations, and four distinct queries. Because generated endpoint deltas are
unequal, every pair distinguishes all three settings; demonstrations alone leave
only the selected setting among those declared rivals. Public challenge names
are SHA-256 hashes of the exact visible demonstrations and query inputs, and
public files omit the setting, program, seed, and query answers.

From the packet extraction directory, run focused portable tests:

```bash
python3 review.py run python3 -m arcpuzzles check db63430eeffa \
  --stage task_tests --phase after --timeout 180 \
  --out ../checks/db63430eeffa-after-task-tests
```

Run the Racket-backed three-setting materializer/verifier:

```bash
cd WORK
python3 run_with_racket.py python3 \
  generators/db63430eeffa/workspace/parametric/verify.py \
  --seed 17 --out ../checks/parametric/db63430eeffa-path-selection-v1
```

The verifier executes the exact default rule on every canonical labeled pair,
executes all three Racket materializations on all seven pairs in every retained
episode, checks them against the Python mirror, verifies declared-rival
identifiability from demonstrations, and writes private episodes plus opaque
public challenges. This bounded evidence does not approve the prototype or
admit it to training.
