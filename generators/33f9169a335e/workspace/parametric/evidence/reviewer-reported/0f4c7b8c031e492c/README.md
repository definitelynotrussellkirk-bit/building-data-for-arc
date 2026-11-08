# Retained execution evidence and reusable check logger

All paths here are relative to `WORK/` unless stated otherwise.

- `parametric/run-v1/report.json` is the compact main result: four episodes,
  nine protected Racket calls, 38 executed pairs, source/runtime hashes and
  per-query certificates.
- `parametric/run-v1/public/` contains challenge JSON only: demonstration
  inputs/outputs and query inputs, named by SHA-256 of exact visible bytes.
- `parametric/run-v1/private/` contains query labels, parameters, full executed
  rules, verifier receipts, the U edge grids and the paired context witness.
- `logs/focused-v2.txt` records the 28 passing prototype unit tests.
- `logs/racket-retention-v1.txt` records the retained Racket run.
- `tickets/` contains only the two assigned bounded supplementary probes.
- `red-*.txt` are expected pre-implementation missing-module failures, not
  unresolved failures. `green-ray-mode.txt` is the first eight-test pass.
- `storage-observations.jsonl` records the private temporary filesystem;
  its explicit limitations distinguish it from the exhausted original host.

## Reproduce after applying the source patch

From the outer extracted packet directory, use a fresh destination and label:

```sh
python3 WORK/checks/log_check.py --label focused-replay -- python3 review.py run python3 -m unittest discover -s generators/33f9169a335e/tests -p 'test_parametric_*.py' -v
python3 WORK/checks/log_check.py --label racket-retention-replay -- python3 review.py run python3 generators/33f9169a335e/workspace/parametric/retain.py --out ../checks/parametric/replay --seed 20261023 --demos 2 --queries 4
```

`log_check.py` is a small reusable wrapper for this packet layout. It records
the payload argv, packet-relative working directory, outer launcher, exit status,
elapsed seconds, selected
source hashes and output log in `RESULTS.json`. A repeated label is rejected
so later runs cannot silently overwrite earlier evidence. Run it sequentially.
Only commands beginning with `python3 review.py run` are accepted. The payload
runs in `repo` relative to WORK; the outer launcher is retained separately.
It does not infer a passing status from generated files.

`retain.py` is the reusable artifact builder: sample -> execute Racket ->
check demonstration-only alternatives -> export visible-byte identities ->
retain private receipts. Its Python transform is an authoring expectation;
the executed Racket result supplies the retained labels. Changing source
requires a fresh run and output directory.
