# Safe diagnostics for blocked solve preparation

Status: **proposed shared-tool change; not installed in the packet**.

## Problem and existing evidence

`prepare_solve()` catches generation errors and reports only `Episode generation
blocked: GenerationFailure`. That protects the visible-only solve, because a
worker exception can contain a private Racket rule or query labels. However, it
also removes the worker exit status, timeout/interruption status, and information
needed to distinguish an incomplete environment from a task problem.

The current implementation already writes the raw exception to
`.review/solve-private/generation-error-NNNN.json` or the corresponding
`solve-private-blind` directory. Those records are **not safe solve-phase
diagnostics**: they may expose forbidden reference content. This proposal does
not read them or make them public. It does not diagnose the packet's actual
initial failure; that cause remains unconfirmed here.

## Proposed change

The optional patch changes only `src/arcpuzzles/review_solve.py` and adds one
generic regression test module. On a blocked preparation it retains and displays
`preparation_diagnostics` containing:

- The failed generation worker's exit code, timeout flag and interruption flag,
  when the exception carries a `GenerationFailure` process receipt.
- The interpreter path and Python version used by a separate diagnostic probe.
- Whether NumPy, Pillow and the selected Racket executable can be discovered in
  that interpreter's isolated environment.
- Whether the diagnostic probe completed; a probe failure never replaces the
  original blocked result.

The probe runs a fixed standard-library script with the same interpreter,
`-E -s`, and `run_process` environment isolation as generation, in a fresh empty
temporary directory. It does not load any task, generator, rule, catalog data or
labels. Python module discovery does not import NumPy or Pillow. Racket discovery
uses `RACKET_PATH` when set, otherwise `PATH`; it does not execute Racket.

These are **post-failure environment observations**, not a causal diagnosis.
Discoverability does not prove that a package imports successfully or that Racket
can execute the task. A process may fail even when every listed prerequisite is
discoverable. The probe also intentionally does not reproduce imports from a
task's staged directory.

The CLI projects only named fields with exact expected types. Worker stdout,
stderr, commands, exception messages, partial episodes and future unknown fields
remain excluded. Existing numbered failure receipts, deterministic seed behavior,
private error retention and the blocked exit status remain intact.

## Files

- `prepare-diagnostics.patch`: optional maintainer patch, relative to repository
  root. Keep separate from the assigned task's `patches/source.patch`.
- `review_solve.proposed.py`: runnable candidate source for isolated verification.
- `test_prepare_diagnostics.py`: synthetic failure and secrecy regressions.
- `evidence.json`: source hashes, exact test commands, outcomes and limitations.
- `baseline.*`: the nine expected baseline regression failures.
- `proposal.*`: focused tests against the candidate.
- `visibility.*`: the existing CLI visibility tests against the candidate.
- `replay.*`: patch application and tests against the applied candidate.
- `default-python-pytest-unavailable.log`: the initial failed test invocation;
  the packet virtual environment was then used successfully.

All fixtures are synthetic. No real task source, authority, private receipt or
hidden answer was opened, and no preparation command was run on the real packet.

## Reproduce without editing the active repository

From the outer extraction directory, after installing the declared test
prerequisites in `WORK/.venv`:

```sh
ARCPUZZLES_REVIEW_SOURCE="$PWD/WORK/repo/src" \
PREPARE_TARGET_SOURCE="$PWD/WORK/checks/tooling/prepare-diagnostics/review_solve.proposed.py" \
PYTHONDONTWRITEBYTECODE=1 \
WORK/.venv/bin/python -m pytest -q -p no:cacheprovider \
  WORK/checks/tooling/prepare-diagnostics/test_prepare_diagnostics.py

ARCPUZZLES_REVIEW_SOURCE="$PWD/WORK/repo/src" \
CLI_TARGET_SOURCE="$PWD/WORK/checks/tooling/prepare-diagnostics/review_solve.proposed.py" \
PYTHONDONTWRITEBYTECODE=1 \
WORK/.venv/bin/python -m pytest -q -p no:cacheprovider \
  WORK/repo/tests/test_review_solve_cli_visibility.py
```

After maintainer adoption, rerun the focused modules in the normal checkout.
Full repository tests were intentionally not run during the blind-only lane;
they can exercise real generators/reference material outside this task's scope.

## Reading the diagnostics

If Racket is undiscoverable, run `python3 review.py setup` from the outer packet
directory, then retry the same preparation. If NumPy or Pillow is undiscoverable,
check/install prerequisites in the displayed interpreter with
`PYTHONNOUSERSITE=1`. A worker timeout or interruption is separately reported.
When prerequisites are discoverable and generation still fails, retain the
blocked result for maintainer analysis of the private receipt; do not inspect
private error text to solve the puzzle.

The probe adds at most its 10-second execution allowance plus normal process
termination grace, only after a failed preparation. No new dependency, network
request, resource preflight, seed change or assignment change is introduced.
