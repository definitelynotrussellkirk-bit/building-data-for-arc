# Reusable review probes

Run all commands below from the extracted packet root. `run_with_racket.py`
selects the packet runtime and changes the child working directory to `repo`.
No package installation or network request is needed once offline Racket and
existing Python dependencies are available.

## Focused tests (not discovered by the normal repository suite)

```bash
python3 -m pytest -q repo/generators/4a3ababcaceb/tests
```

## Source-bound, reference-backed lesson gate

```bash
python3 run_with_racket.py python3 generators/4a3ababcaceb/workspace/contrast_probe.py --samples 120 --lessons 30 --require-refutation --out ../checks/contrast-after.json
```

`--generator ../checks/baseline_generator.py` tests the preserved original
source. With `--require-refutation`, the original is expected to exit 1 and the
reviewed version 3.1 source to exit 0. Without the flag, this is an observational
census: a zero process exit only establishes successful reference/validator
execution, not lesson refutation. Inspect `refutation_gate` and `failures`.

The probe copies the selected runtime, invokes canonical Racket for each label,
uses independent Python rival implementations, records source/rule hashes and
actual temporary cwd/sys.path, and saves a concrete output disagreement for each
rival found in the ordinary sample. Normal seeds begin at 12000; lesson seeds at
22000. Counters are evaluations; a separate unique-input count exposes repeated
default/medium or anchor examples. Default counts mean 963 reference executions.
For a cheap smoke use `--samples 1 --lessons 1`.

The gate fails for a surviving rival, missing/nonpositive lesson denominator,
missing rival/band, invalid counts, or reference/validator failure. It does not
exhaust all algorithms or guarantee arbitrary externally assembled lessons.
Profiles and one-cell source clutter still warrant composite-heuristic probes.

## Findings-only audit reproducer

```bash
python3 run_with_racket.py python3 generators/4a3ababcaceb/workspace/audit_probe.py --out ../checks/audits.json
```

This intentionally targets the immutable audit draw e46c2557ad08 and bb41378fe3c8;
it is not a random reassignment. It stages both runtimes without modifying their
generators. It reports the override-range exception, exact marker underfill,
documentation/domain qualifiers, color-blind and overwrite rivals, and actual
Racket labels. Exit zero means the probe completed without reference-mirror
errors; audit contract defects remain findings in its JSON.

Neither probe belongs in the visible-only solve phase: both intentionally access
reference code for verification. Use only `solve/challenge.json` and the Python
candidate/probe when fulfilling that separate step.
