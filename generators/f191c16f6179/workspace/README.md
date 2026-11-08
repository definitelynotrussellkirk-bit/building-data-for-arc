# Workspace

The selected implementation is `../generator.py`. Workspace tools do not
replace the reference Racket labeler.

## Exact-control probe

From the extracted review packet's outer directory:

```sh
python3 review.py run python3 generators/f191c16f6179/workspace/probe_contract.py --full-grid --seeds 2 --out ../checks/joint-controls-new.json
```

The wrapper executes in `WORK/repo`. The full probe checks every height and
width in 5..16, paired-color count in 1..5, three difficulty bands, seeds 0..1,
and sample indices 0..2: 12,960 draws. It measures dimensions and color counts
independently from pixels, verifies self-check/observer agreement, counts exact
unique inputs, checkpoints progress and binds the report to source SHA-256.
This checks the generator's control contract; it does not verify output labels.
An existing output is refused so earlier failures cannot be overwritten.

For quicker boundary checks, omit `--full-grid`; use `--help` for options.
Future agents can adapt the small axis specification and pixel observations
to another task without changing production or shared runtime files.

## Focused tests

```sh
python3 review.py run python3 -m pytest -q generators/f191c16f6179/tests
python3 review.py check --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-new
```

The second command snapshots and tests the portable layout. Install pytest in
the Python interpreter named by its result if that runtime lacks it. The tests
use `reviewer_support.find_root` and canonical helpers and must not be imported
during a visible-only solve episode.
