# Task workspace

The selected implementation is `../generator.py`. Workspace tools are optional
review aids; they do not change the rule, shared runtime or approval.

## Canonical feature-support probe

`probe_canonical_support.py` is a standard-library, opt-in input diagnostic.
Its reusable `compare_support(canonical_rows, generated_rows_by_band)` compares
consistent dictionaries of type-sensitive JSON scalar features and warns when a
canonical value is absent in a sampled band. Malformed data is rejected; existing
output files are never overwritten.

The task-specific adapter measures equal/unequal normalized bounding boxes,
complete blank internal rows/columns and their conjunction, and whether every
shape has five cells. It reads input pixels only. Other tasks need their own
reviewed extractor; do not apply this fixed-color adapter globally.

From `WORK/repo`, using Python 3.12 with the packet runtime available:

```sh
python3 generators/2a1d414bfe10/workspace/probe_canonical_support.py \
  --generator generators/2a1d414bfe10/generator.py \
  --per-band 100 --out ../checks/support-new.json
```

Or from the extracted outer folder:

```sh
python3 review.py run python3 \
  generators/2a1d414bfe10/workspace/probe_canonical_support.py \
  --generator generators/2a1d414bfe10/generator.py \
  --per-band 100 --out ../checks/support-new.json
```

The CLI uses seed 160999 and indices 0 through `per_band - 1` in each band.
Reports bind source, extractor and canonical hashes and retain exact counts and
replay coordinates. Canonical lookup uses `reviewer_support`. The comparator
distinguishes `true`, `1` and `"1"`; an empty canonical dataset provides no
evidence of completeness.

Missing sampled support is a review warning, not a wrong-label finding or proof
of impossibility. Zero warnings do not establish joint coverage, matched
frequencies, label correctness or training performance. Obtain separate Racket
evidence before making a rule-lawfulness claim about a counterexample.

## Focused verification

From the extracted outer folder:

```sh
WORK/.venv/bin/python review.py check --stage task_tests --timeout 600 \
  --phase after --out ../checks/task-tests-new
```

This copies tests and workspace into an isolated runtime and runs both test files.
Use an interpreter with pytest, NumPy and Pillow outside its user site. The general
twelve-stage battery does not include task tests. Root `REVIEW.md`, `DECISIONS.md`
and `RESULTS.json` record actual final commands and evidence. Workspace drafts
are never automatically selected.
