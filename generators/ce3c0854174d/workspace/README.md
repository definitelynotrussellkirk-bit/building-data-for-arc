# Reusable review tools

The transform-legend tools use only Python's standard library. Run from the repository root:

```sh
python3 generators/ce3c0854174d/workspace/transform_legend_probe.py \
  --challenge path/to/challenge.json --out path/to/new-report.json
```

The challenge has ARC-style train input/output pairs and test inputs. Query
output fields are ignored, even if supplied. The tool does not load the generator,
canonical data, Racket, or a saved solution. It assumes a row-0 script, one cropped
body, cumulative transforms from the eight D4 operations, and a top-aligned
gallery separated by single blank columns.

Each visible intermediate state constrains the code's meaning. The tool
intersects those constraints and enumerates mappings needed by each query.
It returns two concrete conflicting predictions for ambiguity. Multiple surviving
legends are accepted when they produce the same query output. Exhausting the
mapping budget is incomplete, never a pass.

Exit codes: 0 = identifiable within this finite family; 1 = ambiguous;
2 = inconsistent data/unsupported grammar/incomplete search.
Output paths must be new. Reports include input/tool hashes and visible
transition evidence. No result proves uniqueness against arbitrary programs.

To check the probe against an already labelled census:

```sh
python3 generators/ce3c0854174d/workspace/validate_legend_probe.py \
  --census path/to/lesson-census.json --out path/to/new-validation.json
```

This verifier feeds the probe only demonstrations and query inputs, then compares
the unique prediction with the retained Racket label. It supports plain JSON or
gzip JSON and reports production and rotation counts separately. It does not
generate new examples or relabel data.

The returned checks/curriculum-before/witness.json is a positive ambiguity
reproducer: the probe must exit 1. The source-bound final census and
checks/legend-probe-validation.json retain 300 production checks and 1,200
query-rotation checks with no prediction disagreement.

Focused tests are in ../tests/. Use the packet's task_tests stage for portable
staging, and retain its prerequisite receipt. A twelve-stage generator battery
does not collect these task-local tests.

## Bounded repository testing

`run_repository_tests_bounded.py` runs the public `tests/test_*.py` files in
separate pytest processes and removes only each process's owned temporary
directory after that process exits. It retains per-file logs, JUnit reports,
exact commands, interpreter identity, exit codes, optional source bindings,
and a checkpointed aggregate report. This avoids retaining every staged
repository fixture until the whole suite finishes on a crowded executor.

Use the packet runtime wrapper and a Python environment whose pytest is available
outside user-site (isolated task-test children disable user-site):

```sh
python3 generators/ce3c0854174d/workspace/run_repository_tests_bounded.py \
  --repo . --out ../checks/new-bounded-run \
  --bind-source generators/ce3c0854174d/generator.py
```

The wrapper preserves the caller's runtime environment. It changes process
batching, so it cannot detect interactions that require multiple test files in
one process. It does not clear global temporary directories or other sessions'
files. An output directory must be new; a timeout or missing JUnit is a failure.
