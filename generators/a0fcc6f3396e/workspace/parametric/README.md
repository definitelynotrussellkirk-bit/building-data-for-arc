# Proposed output-color parameter

**Status: task-local prototype.** The production generator continues to use the
canonical Racket rule. This workspace does not change the production API,
catalog kind, rule authority, or approval hashes.

The task splits the grid at full-height color-9 columns, closes each panel's
nonzero cells across rows and then columns, compares the completed shapes up to
translation, and tightly crops the unique shape. The proposed parameter changes
only the final crop's output color.

| Parameter | Allowed values | Original/default | Input constraints affected |
|---|---|---|---|
| `output_color` | Literal integers `8` and `3` | `8` | None |

At setting 8, `materialize_program` returns the canonical `program_solution`
text exactly. At setting 3, it changes only the final explicit
`(crop-cells (second odd) 8)` argument to 3. The constructor retains background
0, marker color 2, and two full-height separator columns of color 9. The three
panels each contain four rectangle corners; two completed rectangles have equal
dimensions and the third differs. Input sizes remain within 30 by 30.

## Run from the outer extracted packet directory

```bash
python3 review.py run python3 generators/a0fcc6f3396e/workspace/parametric/prototype.py --out ../checks/parametric/run --seeds 0 1
python3 review.py run python3 generators/a0fcc6f3396e/tests/test_parametric.py -v
```

Use a new `--out` directory for another run. The same commands work from `WORK/`
by replacing `python3 review.py run` with `python3 run_with_racket.py`.
Python 3.12 and the included Racket runtime are sufficient for these focused
tests; they use `unittest` and remain collectable by pytest in the task-test gate.

`random.Random(seed).choice((8, 3))` chooses the output color **once per episode**.
Seed 0 selects 3; seed 1 selects the canonical default 8. A separate seeded RNG
varies geometry placements and panel sizes. Each complete episode has three
demonstrations and one query. Demonstrations rotate the odd panel position and
include equal-area/different-shape, shared-height, and shared-width cases.
Every demonstration visibly distinguishes the two allowed output colors.

`prototype_passed` requires complete episodes for both allowed settings as well
as the canonical parity, settings witness, and parameter ambiguity checks. A run
whose checks pass but whose selected seeds cover only one episode setting keeps
all its receipts with status `prototype_partial`, lists the absent setting in
`missing_episode_settings`, and exits with code 1. A failed check has status
`prototype_failed` even when episode coverage is incomplete. The default seeds
0 and 1 cover both settings; executing both programs on a witness alone does not
satisfy complete-episode coverage.

## Retained evidence and privacy boundary

`public/episode-*.json` contains only demonstration input/output pairs and query
inputs. The `private/` directory contains the chosen parameter, seed, query
answers, exact Racket program and callable, hashes, source manifest, legal input
construction, executed rival predictions, canonical parity, and the same-input
settings witness. The root `result.json` is authoring metadata; it is not a
model-facing challenge. Give a solver only the desired file under `public/`.

Every label is executed by `label_worker.py` using `RacketBridge` and the shared
`wrap_rule` pipeline. The public runtime preparer supplies the local parser and
Racket dependencies; the copied selected generator is never imported or called.
The exact request, worker command, exit code, stdout/stderr, runtime manifest,
and Racket runtime identity are retained. No Python output mirror supplies labels.

The default run executes both materialized settings on three labeled canonical
pairs, one lawful settings witness, and eight episode inputs: **24 Racket grid
evaluations**. It compares the default setting against the canonical labels and
checks both declared parameter settings against each episode's demonstrations
and query. A setting fitting all demonstrations but disagreeing on the query is
reported as `ambiguous_query`, never silently accepted. Unsupported colors are
rejected; a changed canonical final recolor causes reassessment rather than an
unverified source mutation.

## Limits

This is bounded evidence for two settings and the listed seeds. It does not
establish arbitrary-seed coverage, exhaustive structural identifiability, a
production parametric interface, or approval of the alternative rule. Prototype
inputs are independently constructed lawful corner rectangles and do not claim
coverage of the repaired production generator. Canonical repair tests and
acceptance remain separate from these focused prototype checks.
