# Review tools for 5ccdbe078da6

Selected implementation: `../generator.py`. None of these tools changes approval,
canonical rules, or training-admission state. Use a fresh output path for replay.
Commands below run from the **original extracted packet root** after applying the
return patch. `run_with_racket.py` changes its child working directory to `repo`.

## Regression tests

```sh
python3 run_with_racket.py python3 -m pytest -q generators/5ccdbe078da6/tests
python3 run_with_racket.py python3 generators/5ccdbe078da6/workspace/review_probe.py --mode portable-tests --out ../checks/replay-portable.json
```

## Racket-labeled census and compact lessons

```sh
python3 run_with_racket.py python3 generators/5ccdbe078da6/workspace/review_probe.py --mode main --per-band 200 --out ../checks/replay-census.json
python3 run_with_racket.py python3 generators/5ccdbe078da6/workspace/lesson_cover.py --report ../checks/replay-census.json --pool-size 20 --max-demos 5 --out ../checks/replay-lessons
```

To compare the immutable old generator too, add
`--baseline ../.review/baseline/repo/generators/5ccdbe078da6/generator.py` to the
census command in the original assigned packet. The baseline is not shipped a
second time in the delta return.

`lesson_cover.py` verifies census/source hashes, deduplicates, separates query
inputs from candidate demonstrations, and solves exact cover over at most 16
named rivals. Failures are retained and return nonzero. The query-output field
is not an input to `select_demos`. Public challenges, research query labels and
provenance are separate files. Do not conflate these research labels with the
fresh reviewer-solve labels, which remain private to its checker.

## Arbitrary-task Racket cases

```sh
python3 run_with_racket.py python3 generators/5ccdbe078da6/workspace/review_probe.py --mode cases --task 5ccdbe078da6 --inputs ../checks/counterexample-5ccdbe078da6.json --out ../checks/replay-counterexample.json
```

Input is a JSON list of objects containing `input` grids. The tool records actual
Racket outputs and validator results. It does not automatically certify an
`expected_output` field: compare that field explicitly. `checks/verify_exports.py`
in this return demonstrates an end-to-end comparison of the 98 exported labels.

## Runtime timeout diagnosis

```sh
python3 run_with_racket.py python3 generators/5ccdbe078da6/workspace/runtime_timeout_probe.py --out ../checks/replay-runtime-startup.json
```

This compares startup/timeout settings in unmodified shared code. It is a
diagnostic, not a substitute passing repository suite. The documented original
run had 169 passed and one failed root test.
