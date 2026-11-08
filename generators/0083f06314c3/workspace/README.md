# Executable review probes

These task-local tools accompany candidate `0083f06314c3` v4.1.0. They are not shared-runtime replacements. Run the commands below from the **extracted packet root**, after applying the return patch. Use Python 3.12+, the packet's documented NumPy/Pillow/pytest dependencies, Bash, Git, and its Racket wrapper. `python3 setup_racket.py` unpacks the bundled verified offline runtime on the supported Linux platform.

## Task regression tests in the real copied layout

```bash
python3 run_with_racket.py python3 generators/0083f06314c3/workspace/review_probe.py \
  --mode tests --out ../checks/replay_tests
```

The launcher uses `prepare_runtime`, explicitly copies this task's `tests` and `workspace` (not yet in the static catalog mapping), and runs all task tests there. It writes `pytest.log`, `pytest.json`, `run.log`, and `runtime.json`, including actual cwd, argv, exit code, and runtime-manifest hash. New imports use only the ordinary copied runtime plus its Python installation. This is not an OS-enforced read sandbox.

## Canonical-consistent rivals, malformed-input rejection, coverage, and parity

```bash
python3 run_with_racket.py python3 generators/0083f06314c3/workspace/review_probe.py \
  --mode census --count 80 --out ../checks/replay_census --racket-all

python3 run_with_racket.py python3 generators/0083f06314c3/workspace/review_probe.py \
  --mode census --count 200 --seed-base 100000 --racket-all --axis-corners \
  --out ../checks/replay_stability
```

`--count` means draws **per difficulty band**. Every draw is regenerated for determinism. `--racket-all` compares every sampled output with actual canonical Racket, not only the Python mirror. `--axis-corners` adds 128 hard-difficulty cases: all min/max combinations of six axes on the even-seed A-overlap and odd-seed B-overlap branches. It checks observed overrides, self-check, and Racket agreement.

Outputs include `census.json`, `interior9.json`, `overlap_counterexample.json`, and, when found, `generated_overlap.json` and `generated_selector1.json`; axis mode adds `axis_corners.json`. The exact hand-built overlap fixture is separate from ordinary emitted witnesses. The interior-9 mutation is intentionally outside the repaired generator domain: the tool records the mirror discrepancy and rejection rather than falsely claiming universal parity. The regression tests enforce the new rejection/coverage requirements; the census mode can also run on the original implementation to measure its deficient baseline without treating every old deficiency as a launcher error.

Census coordinates are `(seed_base+i, sample_index=i)`, which correlates parity and profile. Do not use this census alone as an unbiased estimate of overlap-branch frequencies. Fixed-seed even/odd lesson tests and explicit both-branch corners are complementary.

Racket subprocess execution can outlast short caller tool limits. Preserve partial runs, but count a run only after a terminal receipt (`runtime.json` and the caller's exit record) exists. Use a new output directory for a retry rather than presenting old partial files as fresh results. Commands do not access private solve labels.

## Findings-only audit replay

```bash
python3 run_with_racket.py python3 generators/0083f06314c3/workspace/audit_probe.py \
  --out ../checks/replay_audits --count 80
```

This copies the two assigned audit targets unchanged, builds independent connected-component/gallery predictions, checks a bounded reference sample, exercises the concrete overrides and degenerate textures, and writes one JSON per target plus runtime receipts. It is not a replacement for each target's full battery and it does not patch their sources. The exact grids and reference errors distinguish sampled defaults from deliberate edge cases.

## Pristine-source bootstrap regression replay

```bash
python3 repo/generators/0083f06314c3/workspace/replay_pristine_test.py \
  --source-zip '../SEND-THIS-ARCpuzzles-review(20261002-153616).zip' \
  --out checks/replay_pristine
```

This command requires the original uploaded ZIP, not the small return ZIP. It extracts only untouched `repo/src`, `repo/tests`, `pyproject.toml`, and `README.md` to a temporary directory and runs the single recorded bootstrap test with `PYTHONPATH=src`. It records that actual cwd, argv, output, and exit. In the review's source-only environment it exits 1 with the same `ModuleNotFoundError: arcpuzzles` as the full suite. A different environment with the package installed may behave differently; failure here is evidence about the original source-only fixture, not every deployment.

## What the results mean

A green local test/census run is evidence for its stated cases and source version. It does not establish arbitrary-input equivalence, every-seed termination, model learning gains, private-query correctness, or training admission. The return includes immutable source identity, original failed checks, exact commands, and final reports for independent maintainer replay.
