# Review workspace and replay guide

Selected implementation: `../generator.py`, v2.0.0. This directory is an authoring workspace and is not automatically selected as generator code. The rule and remaining support limits are described in `../notes.md`; focused regressions live in `../tests/test_contour_contract.py`, and the exact joint counterexample is in `../counterexamples/joint_six_rivals.json`.

## Reuse the retained return

The return for assignment `review-069a9b841ebabc26` includes `REVIEW.md`, `DECISIONS.md`, `QUESTION_ANSWER.md`, `AUDIT.md`, `RESULTS.json`, the official source patch, the exposed solve, and source-bound evidence under `checks/`. Apply that patch in the original packet's WORK directory as instructed in RETURN-GUIDE.md. Exact final generator SHA-256:

`92caaf858ae07f4d83f9d097870d1b21b809fedc0c54478ba77c85984b790717`

Use new output paths for new checks. From the outer extraction directory containing `review.py`:

```sh
python3 review.py setup
python3 WORK/checks/tooling/bootstrap_offline_pytest.py --venv WORK/.venv-next-review
WORK/.venv-next-review/bin/python review.py check --stage task_tests --phase after --timeout 600 --out ../checks/next-task-tests
python3 review.py run python3 -m arcpuzzles lesson-census 0ee26bf68bad --enumerate-schedule-period --schedule-seed 0 --rotation-policy require --timeout 1800 --out ../checks/next-schedule.json
python3 review.py check --battery --compact-results --require-rotations-identifiable --schedule-census ../checks/next-schedule.json --schedule-seed 0 --timeout 4000 --phase after --out ../checks/next-after
python3 review.py run python3 -m arcpuzzles lesson-census 0ee26bf68bad --per-band 100 --rotate-query --rotation-policy require --gzip --timeout 1800 --out ../checks/next-lessons.json
```

The offline helper uses the host interpreter's already installed pure-Python pytest dependencies and a new venv. It needs system-site NumPy/Pillow and a launching interpreter that can see the installed distributions. For a clean online environment use the ordinary dependency installation documented by WELCOME.md instead. Keep the portable runner's user-site isolation enabled.

Task tests use `reviewer_support.find_root`, `canonical_pairs` and `load_selected_generator`; they do not infer a repository using fixed parent counts or import private generator aliases. Tests assert the component/contour contract, actual controlled geometry, malformed-input rejection, canonical-fitting rivals, and production/rotation scheduling. The final receipt contains 63 parametrized test cases, not 63 distinct test functions.

## Evidence and next experiments

The six canonical-fitting rivals are declared by the generator. A seventh full-crop rival belongs to the lesson contract but fails the canonical pairs. Future probes should read the declarations, retain exact generator/Racket identities, and label instances using public `arcpuzzles apply`. The current seven-rival result is finite: repeated winner colors and holes in losing objects are useful next support expansions. They must preserve existing witnesses and complete-lesson query-rotation support.

Two earlier large reports in the return are compressed using the supplied `checks/tooling/evidence-compression/evidence_compression.py`. Their manifest maps every raw path, size and SHA-256. Restore into a new directory with `restore --bundle checks/compressed-originals --out /absolute/new/directory`; the final 300-lesson report remains directly readable.

Never consult these authoring helpers, source files or reference labels during a visible-only solve. The retained exposed solve was finished from the same final generator bytes, with earlier source exposure declared and private correctness withheld.
