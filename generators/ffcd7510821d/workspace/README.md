# Reusable review workspace

Apply the return's `patches/source.patch` to its matching packet before using
these tools. Run wrapper commands from **packet_root**; the wrapper changes to
`repo`, sets the included Racket executable, and exposes `arcpuzzles`.

```sh
python3 setup_racket.py
python3 -m pytest -q repo/generators/ffcd7510821d/tests
python3 run_with_racket.py python3 generators/ffcd7510821d/workspace/orbit_census.py --phase maintainer --count 500 --seeds 0 --racket --out ../checks/maintainer-orbit
python3 run_with_racket.py python3 generators/ffcd7510821d/workspace/audit_targets.py --seed 17 --per-band 100 --out ../checks/maintainer-audits
```

Use fresh output directories; the tools refuse to overwrite prior evidence.
`orbit_census.py` accepts `--generator ../checks/baseline_generator.py` to replay
the frozen baseline and a comma-separated `--seeds`. Duplicate seeds are rejected.
It retains every grid/output, all failing lesson windows, source/rule hashes,
runtime identity, and exact denominators. Exit 1 means findings or generation
errors; inspect the summary. Without `--racket`, labels are explicitly marked
Python hypotheses, not authority-backed labels.

`audit_targets.py` is intentionally bound to the two IDs/hashes in this packet's
AUDIT_ASSIGNMENT.json. It retains actual Racket outputs and rival counterexamples;
zero exit means the audit ran, **not** that both targets are clean. Do not use it
as an automatic admission decision or silently retarget another assignment.

Both tools use the public `prepare_runtime` staging API. The source runtime alone
is not a complete runnable import layout. Manifests retain the actual temporary
runtime directory; that temporary directory need not persist after the tool exits.
No environments, private query answers, or installed runtimes belong in the return.

See HANDOFF.md before extending this work. The test suite includes real Racket
CLI staging, pure orbit/lesson checks, and source-bound audit probes.
