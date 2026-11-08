# Reusable authoring tools

The selected canonical implementation is `../generator.py`; workspace prototypes are never automatically selected.

## Shortcut probe

From packet `WORK/`, run:

```sh
python3 run_with_racket.py python3 generators/c5dd8036311b/workspace/probe_shortcuts.py --out ../checks/shortcuts-new
```

Use a fresh output directory. The probe loads the selected module with portable reviewer_support helpers, iterates its actual CANONICAL_SHORTCUTS declarations, verifies every rival against all five usable canonical pairs, and checks a generated witness plus 9×8 and 30×30 accepted-domain witnesses. It obtains authoritative labels via `arcpuzzles apply`, retaining grids, predictions, commands, source hashes, and errors. The hand-constructed witnesses and the genuinely generated witness are explicitly distinguished. Authoring only: never invoke this during a visible-only solve.

## Parametric prototype

See `parametric/README.md`. `prototype.py` exposes the bounded two-height episode generator; `build_evidence.py` builds instantiated Racket rules, complete labeled episodes, all-setting holdout checks, a negative control, and public masked challenges. V2 public exports use matched input replicas across all settings and opaque random IDs. Give learners only the `public/` directory.

## Focused tests

From `WORK/`, use a Python 3.12+ interpreter with pytest, NumPy, and Pillow:

```sh
python3 run_with_racket.py python3 -m arcpuzzles check c5dd8036311b --stage task_tests --phase after --timeout 1800 --out ../checks/task-tests-new
```

The public stage runs the four task-local files in a staged runtime. No repository-depth assumptions or private per_puzzle imports are required. The final retained result is 163 passing tests. The separate 12-stage battery does not automatically include these tests.
