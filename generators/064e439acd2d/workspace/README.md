# Workspace

The selected implementation is `../generator.py`. Workspace files are not
automatically selected as generators.

## Reusable exact-control probe

`probe_override_contract.py` makes 1,528 deterministic calls across 191 cases
and eight seed/index pairs. It checks returned pixels with the independent
observer in `../tests/contract_support.py`, rather than trusting draw metadata.
Coverage includes each legal integer boundary, explicit shapes, difficulty
independence, counts, textures, combined incompatibilities, malformed controls,
negative fixtures, checker behavior and determinism. The report records source
hashes, exact calls, outcomes, unique inputs and the first failure for each case.
It is a finite API/domain probe and does not execute a Racket label oracle.

From the extracted packet's `WORK` directory, choose a new output path:

```bash
python3 run_with_racket.py python3 generators/064e439acd2d/workspace/probe_override_contract.py --out ../checks/override-probe-new.json
```

For normal checkouts, run the script from the repository root with the package
and runtime dependencies installed. The root finder also supports the portable
`puzzle_generators/per_puzzle/TASK/generator.py` layout.

## Focused tests and canonical semantic checks

Run both task-local suites through the supported portable runner:

```bash
python3 run_with_racket.py python3 -m arcpuzzles check 064e439acd2d --stage task_tests --timeout 600 --phase after --out ../checks/task-tests-new
```

The Python interpreter used for this command must have pytest available in its
environment's site-packages. The runner intentionally disables the user site.
Use a proper virtual environment with the declared development dependencies;
do not weaken that isolation. This review's return includes an offline setup
receipt and helper for its existing dependency inventory.

For Racket-backed production and rotation evidence:

```bash
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 064e439acd2d --per-band 100 --rotate-query --timeout 1800 --out ../checks/lesson-census-new.json
python3 run_with_racket.py python3 -m arcpuzzles lesson-census 064e439acd2d --enumerate-schedule-period --schedule-seed 0 --band easy --band medium --band hard --timeout 1800 --out ../checks/schedule-census-new.json
```

The census reads the actual competitor declarations, checks canonical fit, and
retains materialized inputs, real Racket outputs, accepted indices and each
query holdout. The finite rival set, fixed-seed period enumeration and 1,500
unique-input census have different scopes; do not collapse them into a claim of
complete semantic coverage. `../counterexamples/` contains small labelled
witnesses and the original partial-placement defect.
