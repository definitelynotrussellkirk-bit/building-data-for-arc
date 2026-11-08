# Task-local review tools — 59c2f0a5d4a9

The selected implementation is ../generator.py. `lesson_probe.py` is a reusable
verification tool, not a label source or alternate generator. It uses the normal
Python runtime and public Catalog APIs; Racket executes every reference output.

From a packet root, use a new output directory:

```bash
python3 run_with_racket.py python3 -m pytest -q generators/59c2f0a5d4a9/tests/test_generator.py
python3 run_with_racket.py python3 -m arcpuzzles check 59c2f0a5d4a9 --battery --timeout 4000 --phase after --out ../checks/new-battery
python3 run_with_racket.py python3 generators/59c2f0a5d4a9/workspace/lesson_probe.py --out ../checks/new-lessons --lessons 100 --seed 20261003
```

The wrapper's runtime cwd is repo. In an ordinary installed checkout, provide
Racket normally and run the inner commands from the repository root with
PYTHONPATH=src. Required repository runtime dependencies are NumPy/Pillow; pytest
is needed for tests. No new dependency is introduced by this probe.

Read LESSON_PROBE.md for evidence layout and replay. The probe evaluates all
actual CANONICAL_SHORTCUTS/LESSON_COMPETITORS declarations, records 100 actual
lessons per band with three demos and two queries, checks all three cyclic
starts, and distinguishes overlapping windows from unique inputs. Every failed
or incomplete result is retained and produces a nonzero exit when required.

For integration into a matching extracted source packet:

```bash
git apply --check /path/to/extracted-return/patches/source.patch
git apply /path/to/extracted-return/patches/source.patch
```

Run those commands from the packet root; a Git working tree is not required.
Use maintainer intake for divergent sources rather than forcing a patch. The
return's REVIEW.md, DECISIONS.md, QUESTION_ANSWER.md, AUDIT.md, RESULTS.json and
INTAKE.json preserve decisions and evidence. The final generator is unapproved
until independent maintainer review; no tool in this folder changes approval.
