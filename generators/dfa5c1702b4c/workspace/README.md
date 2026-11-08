# Reusable review tools

The selected implementation is `../generator.py`. These tools are diagnostics;
they are not automatically selected as a generator or label authority.

## Sampler and lesson probe

`probe_sampler.py` generates reproducible diagnostic draws, computes an
independent color-bounding-box/set-intersection oracle, discovers the generator's
actual rival namespaces, checks canonical fits, and evaluates cyclic windows
and each held-out query position. Reports bind the generator/probe hashes and
distinguish direct draws, unique inputs, overlapping windows and rotations.
Exit 0 means no declared-rival ambiguity was found in that probe population.
Racket labels and production rejection behavior require the public census.

From the outer extracted packet directory:

```bash
python3 review.py run python3 generators/dfa5c1702b4c/workspace/probe_sampler.py --seed 0 --seed 6 --seed 17 --out ../checks/new-sampler-probe.json
```

Use a new output path. Options include repeated `--seed` and `--band`,
`--starts`, `--samples-per-seed`, and `--generator-path` for a retained source.
The final independent review used seeds 0–39 and `--samples-per-seed 0`;
the required lesson windows still generate their five distinct index positions.

## Lossless evidence compaction

`compact_evidence.py` is a standard-library utility for a completed, unchanged
report. It writes deterministic gzip, retains a verified original outside the
packet, records relative restoration paths/byte counts/SHA-256, and verifies
recovery data before removing the in-packet original. It rejects unsafe paths,
symlinks and existing destinations. It does not coordinate concurrent writers.

Example from the outer packet directory, replacing both example paths:

```bash
python3 WORK/repo/generators/dfa5c1702b4c/workspace/compact_evidence.py compact checks/large-report.json --root WORK --manifest checks/large-report.manifest.json --retain-original /absolute/path/outside/WORK
python3 WORK/repo/generators/dfa5c1702b4c/workspace/compact_evidence.py restore WORK/checks/large-report.manifest.json --root /absolute/path/fresh-restoration
```

The actual compressed original in this return is the before-override report.
Its manifest is
`checks/before/checks/dfa5c1702b4c_before_override_results.manifest.json`.
After extracting the return's evidence bundle, pass that manifest to `restore`
and choose a fresh destination root. The original report is 46,768,312 bytes;
the verified gzip is 864,829 bytes. No failure rows were dropped.

For a final directory-fsync error after unlink, the original path may already
be absent, but the verified external original, gzip and manifest remain.
Earlier failures leave the original path in place. Tests cover the documented
completed-file workflow, round trips, deterministic output, corruption, path
traversal, symlinks and destination collisions.

## Focused tests

Both tools' supporting tests are in `../tests/`. The public isolated stage
must be invoked explicitly; a general battery does not discover these tests:

```bash
python3 review.py check --stage task_tests --phase after --timeout 600 --out ../checks/new-task-tests
```

The isolated worker excludes user-site packages. If needed, prepare a virtual
environment and invoke both `WORK/run_with_racket.py` and its Python payload
using that environment's interpreter, as recorded in the return's RESULTS.
