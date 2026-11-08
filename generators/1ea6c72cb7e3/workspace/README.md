# Reproducible review probes

From the **extracted packet root** (offline Racket initialized by
`python3 setup_racket.py`):

```sh
python3 run_with_racket.py python3 -m pytest -q generators/1ea6c72cb7e3/tests
python3 run_with_racket.py python3 generators/1ea6c72cb7e3/workspace/lesson_probe.py --out ../checks/replay-final.json
python3 run_with_racket.py python3 generators/1ea6c72cb7e3/workspace/lesson_probe.py --baseline ../checks/baseline_generator.py --out ../checks/replay-before.json
python3 run_with_racket.py python3 generators/1ea6c72cb7e3/workspace/audit_targets.py --out ../checks/replay-audits.json
```

These tools refuse to overwrite retained output files. Use new output names.
The wrapper changes cwd to `repo` and sets the shared import/runtime paths.
Each probe stages a real portable runtime and records its actual directory.
They read public canonical data, never `solve/` or private episode labels.
Do not consult these tools during the required fresh solve phase.

## lesson_probe.py

Default: 100 pinned lessons **per band**, three consecutive demonstrations and
one query, plus all three cyclic starts for ten independent seeds per band.
Uses `materialize_lessons -> runner.run_one`, canonical Racket labels, and the
final generator's declared `CANONICAL_SHORTCUTS`/`LESSON_COMPETITORS` directly.
Records every lesson, unique inputs, source/rule/probe hashes, canonical shortcut
parity, and the first demo-fitting/query-disagreeing counterexample.

Exit 0: all declared rivals refuted by demos in this census and no execution
errors. Exit 1: at least one surviving rival. Exit 2: infrastructure/parity or
validation failure. Distinguishes harmless-on-query survival from actual query
ambiguity. A passing finite test is not universal identifiability.

The baseline option replays retained original bytes against **current** rival
functions; it reports both hashes and does not imply those hooks existed before.
The diagnostic Python reference is not an output authority: Racket supplies
all labels, with independent ray-accumulation tests as another cross-check.

## audit_targets.py

Findings-only reproducer for the two immutable assigned audit targets. Default:
20 pinned lessons per band per target and the shared 20-draw/band profile floor.
Includes canonical counterexamples and generated ambiguous lessons with actual
Racket/rival outputs, exact seeds, validator results, and source binding.

**Exit 0 means execution success, not a clean audit.** Read target profile
verdicts, rival counts, and override findings. Neither target is modified.
One-run-only shortcut generalizes perfectly across sampled generated run grids
but fails all canonical multi-run pairs; echo boundary events sometimes fail
to distinguish toroidal wrapping even when a boundary source is present.

## Evidence retention

Each `.lessons.jsonl.gz` has a report-level original path, expanded byte count,
SHA-256, compressed SHA-256, and restoration command. Decompress exactly as
specified before comparing hashes. Failed red tests, intermediate source,
and the failed override battery remain in the return. Never equate process
exit status with semantic pass or promote training approval from this report.
