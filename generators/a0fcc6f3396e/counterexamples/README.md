# Retained shortcut counterexample

`same-height-odd-left.json` contains a lawful four-corner input and its output executed by the unchanged canonical Racket rule. Two canonical-fitting rivals select the third 3×3 panel; the correct answer is the first panel's solid 3×5 rectangle. This manually constructed query demonstrates an ambiguity in canonical demonstrations. It is not a sampled production lesson or a frequency estimate.

The full execution receipt, all three canonical labeled pairs, and standalone authoring replay are in the review return under `checks/teaching-counterexample/`. The task regression `test_retained_same_height_left_query_refutes_canonical_shortcuts` checks the exact retained query and canonical fit. The schedule regression checks that every held-out pair in the repaired nine-pair cycle leaves demonstrations refuting all declared rivals.

Run the portable task-test gate from the outer packet directory:

```bash
python3 review.py run python3 -m arcpuzzles check a0fcc6f3396e --stage task_tests --phase after --timeout 600 --out ../checks/task-tests-replay
```

Use an environment with the repository's NumPy, Pillow, and pytest prerequisites installed, and choose a new output directory for each run.
