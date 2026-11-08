# Task-local review tools

`reference_probe.py` is an independent geometry oracle for task `96d4a788da47`.
It deliberately does not import `generator.py`; portable tests load the selected
source through `reviewer_support.load_selected_generator`.

Useful checks from `WORK/repo/`:

```bash
python3 -m pytest -q generators/96d4a788da47/tests/test_generator.py
python3 -m arcpuzzles check 96d4a788da47 --stage task_tests --phase after --out ../checks/task-tests
```

The retained counterexample at `../counterexamples/bbox-fill-left.json` is bound
to the final generator SHA and rule hash. It demonstrates why filled bounding
boxes are not a valid substitute for preserving each irregular object's cells.

The helper exposes:

- `slide_left_reference(grid)`: independent cell-preserving translation oracle;
- `bbox_fill_left_rival(grid)`: canonical-fitting shape-destroying shortcut;
- `color_components(grid)` and `observed_axes(grid)`: reusable inspection;
- canonical-pair loading through the public portable support API.
