# Passive exact-override replay probe

This is a proposed reusable reviewer tool, kept outside shared source. It executes
bounded input-generation cases and checks observable override contracts. It does
not produce reference labels, modify generators, or replace a full battery.

## Public interfaces and supported scope

The script uses public `Catalog.describe` to resolve a task's selected source and
portable `reviewer_support.find_root` to bind the supplied library. It loads source
with the Python standard library, with a local package context for task-relative
imports. No private runner imports or copied runtime trees are used.

`generate_input` is a small **local adapter** to the documented per-puzzle
`module.generate(seed, sample_index, difficulty=..., **overrides)` interface;
this checkout has no public helper named `generate_input`. Each returned grid is
then passed to `self_check` and `observe_overrides`. Missing or failing validator
or observer APIs are recorded as failed acceptances, not successful coverage.
Generators exposing only `generate_task` are outside this prototype's API scope.

Requires Python 3.12+, the repository/runtime dependencies of the chosen generator,
and POSIX `fork`. Trusted source is imported once; every individual case executes
in a fresh child with a timeout. The parent terminates timed-out workers. The
sweep also has an explicit case-count cap and wall-time budget.

## Case format

Supply a JSON list of objects:

```json
[
  {
    "id": "boundary_case",
    "overrides": {"grid_h": 8, "grid_w": 8, "palette_size": 10},
    "expect": "accepted"
  }
]
```

Each object has a unique string `id`, an `overrides` object, and optional
`expect` (`accepted`, the default, or `incompatible`). The tool accepts an
incompatibility only when a `ValueError` matches the generator's public
`INCOMPATIBLE_OVERRIDE_COMBINATIONS` or carries a structured set of incompatible
axis names. Unexpected rejection, unexpected acceptance, timeout, invalid ARC
grid, validator messages, observer errors, and exact-value mismatches fail visibly.

The comparison covers integer, boolean, and color axes; explicitly exact axes;
and every supplied override key exposed by `observe_overrides`. Unobserved
string/float controls are not silently reinterpreted as exact quantities.
Their behavior remains the generator/validator's responsibility. This tool does
not independently reverse-engineer categorical geometry.

Seed ranges are increasing with an **exclusive** stop. `--sample-index` and
`--difficulty` are repeatable; the matrix combines them with every seed and
every JSON case. `--difficulty none` passes Python `None`.

## Recorded experiment

The common `cases.json` contains three accepted boundary cases and one declared
incompatibility. Both main sweeps used seeds 0 through 127, sample index 0, and
difficulty `None`: **512 calls per source**.

| Evidence | Returned grids | Declared incompatibilities | Generation/worker errors | Failed cases | Exit |
|---|---:|---:|---:|---:|---:|
| `intermediate_failure.json` | 384 | 128 | 0 | 1 | 1 |
| `final_success.json` | 384 | 128 | 0 | 0 | 0 |

The retained intermediate source fails at seed **114** in
`dense_scatter_palette`: `palette_size=10` is accepted, its validator reports no
error, and the actual observer reports **9**. The first failure includes the
complete arguments, input grid, input hash, and exact mismatch. The final selected
source passes the same bounded sweep.

A second task was also exercised with `second_task_cases.json`; its two calls
passed, demonstrating that the loader and observer comparison are parameterized
rather than hardcoded to the main task.

## Replay

From `WORK/repo`, use fresh output paths because existing evidence is never
overwritten:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:shared/runtime \
python3 ../checks/tooling/exact_override_probe.py 09636f05e06e \
  --library . --cases ../checks/tooling/cases.json \
  --seed-start 0 --seed-stop 128 --difficulty none \
  --max-cases 512 --max-seconds 120 --case-timeout 2 \
  --generator-file ../checks/palette-probe/intermediate_generator.py \
  --out ../checks/tooling/replay/intermediate.json
```

The expected exit is 1, with seed 114 retained as a failure recipe. To test the
selected final source, omit `--generator-file`:

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src:shared/runtime \
python3 ../checks/tooling/exact_override_probe.py 09636f05e06e \
  --library . --cases ../checks/tooling/cases.json \
  --seed-start 0 --seed-stop 128 --difficulty none \
  --max-cases 512 --max-seconds 120 --case-timeout 2 \
  --out ../checks/tooling/replay/final.json
```

The expected exit is 0 for the recorded final source. Exact source, script, and
case-file hashes are stored in each receipt. To reproduce just the failing seed,
use `--seed-start 114 --seed-stop 115` with the intermediate source and another new
output path.

## Output interpretation

Results are strict JSON (`allow_nan=False`). A report contains source identity,
the real command/cwd, complete limits, case definitions, every attempted case,
input hashes, observations, first failure, and the full failure list. Successful
rows reference their full override dictionary through `case_id`; failed recipes
add the complete call arguments directly.

`accepted` counts calls that returned an input, including any failed acceptance.
`incompatible` counts declared/structured rejections. `error` counts other
generation failures, worker failures, or timeouts. `failed` additionally includes
validator, observer, exact-override, and expectation failures.
A time-limited partial sweep has `complete=false` and cannot pass.

Input hashes use SHA-256 over normalized list-of-list grids serialized as compact
ASCII JSON. Full grids are retained for failed accepted calls. Exact shell
commands, environments, process exit codes, elapsed wall times, and console
output from the actual runs are in `command_receipts.json`.

These finite sweeps establish only their recorded cases and source bytes. They
do not certify arbitrary seeds, production lesson sampling, reference semantics,
or cross-case mutable state, since calls use fresh workers.

