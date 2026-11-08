# Smallest-object review tools

These are developer diagnostics, not an alternative training-label path. Labels
come from the packet's canonical Racket implementation. Python alternatives are
explicitly measured rivals. No catalogs, approval records, or shared tools are
modified by these commands.

## Racket-backed rival probe

From the extracted packet root, after `python3 setup_racket.py`:

```sh
python3 repo/generators/ba988f8d25d5/workspace/rival_probe.py \
  --seed 20260928 --per-band 300 --out checks/focused/rivals-new.json
```

The tool prepares a fresh copied runtime using the existing catalog mapping;
executes actual Racket labels for every easy/medium/hard sample and canonical
pair; distinguishes agreement, disagreement and execution errors; retains first
exact counterexamples with replay coordinates; and writes JSON plus an offline
HTML grid report. Existing evidence paths are never overwritten. It records
source SHA-256s, rule identity, seed, sample indexes, realized unique input/output
counts and optional observable target-size histograms.

For a frozen-baseline comparison using the same rival definitions:

```sh
python3 repo/generators/ba988f8d25d5/workspace/rival_probe.py \
  --generator-file .review/baseline/repo/generators/ba988f8d25d5/generator.py \
  --rivals-file repo/generators/ba988f8d25d5/generator.py \
  --seed 20260928 --per-band 300 --out checks/focused/rivals-baseline-new.json
```

For another generator, use `--task-id ID` and a provider module containing
`SEMANTIC_RIVALS = {"name": callable}` through `--rivals-file`. Each callable
accepts one input grid and returns a predicted output grid. Providers must return valid rectangular ARC grids; the probe catches execution
exceptions but does not replace a provider output-schema validator. The module is
trusted local Python, not sandboxed untrusted code. The tool belongs inside an ARCpuzzles
repo because it discovers `src/arcpuzzles` and the runtime mapping. A supplied
`RACKET_PATH` is also added to PATH; otherwise it uses this packet's installed
runtime. `--start-index` changes the replay window. Exit 0 means no generator,
canonical, mirror or rival execution errors, not that all possible shortcuts were
eliminated. Zero disagreements is a finite-cohort finding only.

In the baseline, no `observe_overrides` hook exists, so `target_sizes` is empty
(unavailable), not a claim of zero target cells. Baseline and revised generators
use different versions and distributions: matching seed/index is reproducible,
not a paired identical-input experiment. No statistical or model-score gain is
inferred from these measurements.

## Assigned findings-only audits

```sh
python3 repo/generators/ba988f8d25d5/workspace/audit_assigned.py \
  --out checks/audits/assigned-new.json
```

This is deliberately bound to this packet's immutable two-target audit contract.
It verifies audited source hashes before copying a runtime, checks 100 samples per
band against actual Racket plus independent diagnostic formulas, checks canonical
pairs, and captures exact override and malformed-input reproductions. It does not
fix either audited generator. A different assignment should get a different
case file rather than silently reusing these targets.

## Regression tests

```sh
python3 -m pytest -q -p no:cacheprovider repo/generators/ba988f8d25d5/tests
```

The task tests use an independent object implementation, check the exact boundary
Cartesian product and every sliding three-demo window in the retained test cohort,
exercise malformed inputs and negative fixtures, and verify source authority.
Probe tests check exception accounting, input isolation and HTML escaping. The
standard repo test command does not discover these task-local tests; run both.

The end-to-end authority is still the repository battery:

```sh
python3 run_with_racket.py python3 -m arcpuzzles check ba988f8d25d5 \
  --battery --phase after --out ../checks/after-new
```
